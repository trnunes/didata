import re
import os
import copy
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from string import punctuation
from nltk.metrics.distance import jaro_winkler_similarity
from nltk.corpus import wordnet, mac_morpho
from nltk.tree import ParentedTree, Tree

import unidecode
import itertools
import pickle
import pandas as pd

tagger = None

def get_syn(word):
    # return [word]
    synsets = wordnet.synsets(word.lower(), lang='por')
    synonyms = [word]
    for synset in synsets:
        synonyms += [l.name() for l in synset.lemmas(lang='por')]
    return synonyms

def analyze_entities(text, hints):
    pt_stopwords = stopwords.words('portuguese') + list(punctuation)
    tokens = word_tokenize(hints)
    non_stop_tokens = [t for t in tokens if t not in pt_stopwords]
    synonyms = []
    for t in non_stop_tokens:
        synsets = wordnet.synsets(t.lower(), lang='por')
        if synsets:
            synset = synsets[0]
            synonyms += [l.name() for l in synset.lemmas(lang='por')]
    all_words = non_stop_tokens + synonyms
    text_tokens = word_tokenize(text)
    words_present = [w for w in all_words if w in text_tokens]
    words_not_present = all_words - words_present
    results = {'words_present': words_present, 'remaining_words': words_not_present}
    return results

def load_or_train_postagger():
    global tagger
    if tagger:
        return tagger
    tagger = load_postagger()
    
    if not tagger:
        tagger = train_postagger()
    
    return tagger

def get_parser(grammar):
    return nltk.RegexpParser(grammar)


def get_grammar():
    return (
        '''
          
            NER: {<ART>?<PR.*>?<NE>}
            NP: {<ART>?<PR.*>?(<N.*><PREP.*>?)<ADJ>?<PCP>?}
            NP: {<ART>(<ADJ>|<PCP>)}
            VP: {<NP>?<ADV>?<ART>?<:>?<->?(<V>(<,>|<KC>)?)+}
            CPL: {(<PREP.*>|<N.*>|<NPROP>|<PCP>|<PRO-KS-REL>|<ADV>)*}
            STMT: {<VP>((<,>|<KC>)?<CPL> )*}
            
        '''
    )


def get_domain_phrase(id, domain_phrases):
    
    index = None
    
    if not domain_phrases or not "phr" in id.lower(): return id
    try:
        index = int(id.lower().replace("phr", ""))
        return domain_phrases[index]
    except:
        return id  
    
def get_domain_phrase_id(domain_phrase, domain_phrases):
    return "PHR%d"%domain_phrases.index(domain_phrase.strip())

def train_postagger():
    tagger = nltk.UnigramTagger(mac_morpho.tagged_sents())
    tagger_file = "tagger.pkl"
    with open(tagger_file, mode="wb") as file:
        pickle.dump(tagger, file)
    return tagger

def load_postagger():
    try:
        with open("tagger.pkl", mode="rb") as file:
            return pickle.load(file)
    except FileNotFoundError:
        return None

def tokenize(text):
    return word_tokenize(text)

def sentence_tokenize(text):
    return sent_tokenize(text)

def get_stemmer():
    return nltk.stem.RSLPStemmer()

def stem(tokens):
    tokens_cp = tokens.copy()
    stemmer = get_stemmer()
    return [stemmer.stem(token.lower()) for token in tokens_cp]

def normalize(token):
    if not token or pd.isnull(token):
        return ""
    stemmer = get_stemmer()
    # 
    return unidecode.unidecode(stemmer.stem(token.lower()))

def has_corref_art_keyword(t_index, domain_phrase, tokens):
    tagger = load_or_train_postagger()
    tagged_tokens = tagger.tag(tokens)
    dphrase_tokens = tokenize(domain_phrase)
    classes_to_skip = ("N", "NPROP", "V", "PCP", "ADJ")
    if tagged_tokens[t_index][1] in classes_to_skip:
        return False
    
    if t_index < len(tokens):
        
        next_token = normalize(tokens[t_index+1])
        dtoken_found = [dtoken for dtoken in dphrase_tokens if jaro_winkler_similarity(normalize(next_token), dtoken) > 0.85]
# 
        if dtoken_found:
            return True
    return False

def token_is_reification(t_index, domain_phrase, tokens):
    domain_phrase_parts = tokenize(domain_phrase)
    token_to_compare = tokens[t_index]
    last_domain_phrase_part = domain_phrase_parts[-1]
    prepositions = ["das", "dos", "da", "do", "de"] 
    if token_to_compare in prepositions:
        next_token = tokens[t_index + 1]
        if match_syn(last_domain_phrase_part, next_token):
            return True
    return False

def phrase_is_reification(t_index, domain_phrase, tokens):
    domain_phrase_parts = tokenize(domain_phrase)
    token_to_compare = tokens[t_index]
    last_domain_phrase_part = domain_phrase_parts[-1]
    prepositions = ["das", "dos", "da", "do", "de"] 
    
    if [d for d in domain_phrase_parts if d in prepositions]:
        if match_syn(last_domain_phrase_part, token_to_compare):
            return True

    return False

def intersect_tokens(array1, array2, matching_function):
  return [(elem, i) for i, elem in enumerate(array1) if any(matching_function(elem, elem2) for elem2 in array2)]


# custom equal function
def match(token1, token2):
    token1 = normalize(token1)
    token2 = normalize(token2)
    if token1 == token2:
        return True
    if jaro_winkler_similarity(token1, token2) >= 0.85:
        return True
    return False


def find_candidate_matches_v2(tokens, domain_phrases, search_corref=False):
    domain_phrases_cp = domain_phrases.copy()
    candidates = []
    for domain_phrase in domain_phrases_cp:
        domain_phrase_parts = tokenize(domain_phrase)
        window_size = len(domain_phrase_parts)
        index = 0
        while index < len(tokens) - window_size:
            window_tokens = tokens[index:index+window_size]
            matched_tokens_and_indexes = intersect_tokens(window_tokens, domain_phrase_parts, match)
            slide = index
            matched_tokens_unique = set([normalize(t) for t, i in matched_tokens_and_indexes])
            
            if len(matched_tokens_unique) >= window_size:
                
                matched_tokens = [token for token, i in matched_tokens_and_indexes]
                indexes = [i + index for token, i in matched_tokens_and_indexes]
                min_and_max_indexes = (min(indexes), max(indexes))
                if len(indexes) == 1:
                    min_and_max_indexes = (indexes[0], indexes[0])
                candidates.append(tuple([matched_tokens, domain_phrase, tuple(min_and_max_indexes)]))
                slide = min_and_max_indexes[1]
            index = slide + 1
    return candidates
    
def token_match(token1, token2):
    norm_token1 = normalize(token1)
    norm_token2 = normalize(token2)
    return (norm_token1 == norm_token2) or (jaro_winkler_similarity(norm_token1, norm_token2) > 0.9)

def match_syn(token1, token2):
    syns1 = get_syn(token1)
    syns2 = get_syn(token2)
            
    for syn1 in syns1:
        for syn2 in syns2:
            if(token_match(syn1, syn2)):
                return True
  
    return False
            
def find_candidate_matches(tokens, domain_phrases, search_corref=False):
    domain_phrases_cp = domain_phrases.copy()
    candidates = []
    t_index = 0
    while(t_index < len(tokens)):
        token = tokens[t_index]
        
        for domain_phrase in domain_phrases_cp:
            domain_phrase_parts = domain_phrase.strip().split(" ")
            d_index = 0
            rec_phrase = []
            while (d_index < len(domain_phrase_parts)) and ((t_index + len(domain_phrase_parts)) <=  len(tokens)):
                next_token = tokens[t_index + d_index]
                next_norm_token = normalize(next_token)
                rec_phrase.append(next_token)
                domain_token = domain_phrase_parts[d_index]
                
                if not domain_token:
                    continue
                
                if token_match(domain_token, next_norm_token):
                    d_index += 1
                    continue

                
                
                # if match_syn(domain_token, next_norm_token):
                    # d_index += 1
                    # continue
                
                break
                
                
            is_a_match = (d_index == len(domain_phrase_parts))

            if is_a_match:
                
                firts_last_indexes = (t_index, t_index + d_index - 1)
                candidates.append((rec_phrase, domain_phrase, firts_last_indexes))
                t_index += d_index - 1
                continue
            # import pdb;pdb.set_trace()
            if t_index < (len(tokens) - 1) and search_corref:
                is_a_match =  has_corref_art_keyword(t_index, domain_phrase, tokens)

                if is_a_match:
                   firts_last_indexes = (t_index, t_index + 1)
                   rec_phrase = [token, tokens[t_index + 1]]
                   candidates.append((rec_phrase, domain_phrase, firts_last_indexes))
                   t_index += 1
                   continue
            if t_index < (len(tokens) - 1):
                if(token_is_reification(t_index, domain_phrase, tokens)):
                    rec_phrase = [tokens[t_index -1], token, tokens[t_index + 1]]
                    firts_last_indexes = (t_index - 1, t_index + 1)
                    candidates.append((rec_phrase, domain_phrase, firts_last_indexes))
                    t_index += 1
                    continue
                if(phrase_is_reification(t_index, domain_phrase, tokens)):
                    rec_phrase = [tokens[t_index - 1], tokens[t_index]]
                    firts_last_indexes = (t_index - 1, t_index)
                    candidates.append((rec_phrase, domain_phrase, firts_last_indexes))
                    t_index += 1
                    continue
            
            
        t_index += 1

    return candidates


def annotate_phrases(text, matches, domain_phrases):
    phrase_dict = {}
    for match in matches:
        matched_tokens, matched_domain_phrase, indexes = match
        phrase_id = get_domain_phrase_id(matched_domain_phrase, domain_phrases)
        text = text.replace(" ".join(matched_tokens), phrase_id + " ")
        phrase_dict[phrase_id] = matched_tokens

    return (text, phrase_dict)


def preprocess(text, replace_alt_markup=True):
    
    if not text or pd.isnull(text):
        return ""
    punctuations = [".", "!", "?"]
    if not text[-1] in punctuations:
        text = text.strip() + "."
    replacements = ["\\", "-", "+", "@", "#", "$", "&", ";" ]
    if replace_alt_markup:
        text = text.replace(";", "|")
        text = text.replace("| ", "|")
        text = text.replace(" |", "|")
    for r in replacements:
        text = text.replace(r, "")
    return text

def infer_class(tag):
    if tag[1] == "NPROP" and tag[0] in ("de", "da", "do", "das", "dos"):
        return (tag[0], "PREP")
    if tag[1]:
        return (tag[0], tag[1])
    
    if "PHR" in tag[0]: 
        return (tag[0], "NE")
    else:
        return (tag[0], "N")

def extract_subject(tree):
    subject_tokens = []
    subject_trees = [t for t in tree.subtrees() if t.label() in ["NER"]]
    
    if not subject_trees:
        subject_trees = [t for t in tree.subtrees() if t.label() in ["NP"]]

    for tree in subject_trees:
        subject_tokens += tree.leaves()
    
    return subject_tokens

def cpl_ends_with_neg_adv(cpl_tokens):
    return normalize(str(cpl_tokens[-1])) == "('nao', 'adv')"
    
def parse_stmt(tree):
    triples = []
    
    for stree in tree.subtrees():
        if stree.label() == "STMT":
            subject_tokens = []
            predicate_tokens = []
            object_tokens = []
            
            complement_subtrees = [t for t in stree.subtrees() if t.label() == "CPL"]
            verb_phrase_subtrees = [t for t in stree.subtrees() if t.label() == "VP"]
            subject_candidate = [t for t in verb_phrase_subtrees[0].subtrees()][0]
            subject_tokens = extract_subject(subject_candidate)
    
            for vp in verb_phrase_subtrees:
                sub_phrase = find_subordinate_verb_phrase(vp)
                
                if sub_phrase:
                    predicate_tokens = sub_phrase
                    break
                
                predicate_tokens += [leaf for leaf in vp.leaves() if  leaf[1] in ("ADV", "V", "KC", ",")]


            additional_discovred_triples = []
            for cpl in complement_subtrees:
                
                if cpl_ends_with_neg_adv(cpl.leaves()):
                    cpl_subtrees = [s for s in cpl.subtrees() if s.label() == "NP"]
                    cpl_tokens = []
                    [cpl_tokens.append(t) for s in cpl_subtrees for t in s]
                    if cpl_tokens or predicate_tokens or object_tokens:

                        triples.append([cpl_tokens, predicate_tokens, object_tokens, "N"])
                        
                        break
                prep_stmts = [s for s in cpl.subtrees() if s.label() == "STPREP"]
                if prep_stmts:
                    for p_stmt in prep_stmts:
                        nps = [np for np in p_stmt.subtrees() if np.label() == "NP"]
                        [object_tokens.append(t) for s in nps for t in s.leaves() if t[1] in ("N", "NE", "ADJ", "PCP", "NPROP" )]
                        # import pdb;pdb.set_trace()
                        break
                    
                prep_stmts2 = [s for s in cpl.subtrees() if s.label() == "STPREP2"]
                if prep_stmts2:
                    if prep_stmts:
                        for p_stmt in prep_stmts2:
                            nps = [np for np in p_stmt.subtrees() if np.label() == "NP"]
                            s = [ t for t in nps[0].leaves() if t[1] in ("N", "NE", "ADJ", "PCP", "NPROP")]
                            p = [object_tokens[-1]]
                            o = [ t for t in nps[1].leaves() if t[1] in ("N", "NE", "ADJ", "PCP", "NPROP")]
                            # import pdb;pdb.set_trace()
                            additional_discovred_triples.append([s, p, o])
                if not prep_stmts:
                    object_tokens += cpl.leaves()


            
            if subject_tokens or predicate_tokens or object_tokens:
                triple = [subject_tokens, predicate_tokens, object_tokens]
                
                triples.append(triple)
            if additional_discovred_triples:
                triples += additional_discovred_triples
    return triples

def get_non_stop_tokens(tokens):
    
    return [token for token in tokens if token[1] in ["N", "ADJ", "NPROP", "NE", "PCP", "V"]]

def remove_stop_tokens(tokens):
    pt_stopwords = stopwords.words('portuguese') + list(punctuation)
    return [t for t in tokens if t not in pt_stopwords]

def has_intersection(phrase1, phrase2):
    phrase1_ary = [phrase1, normalize(phrase1)]
    phrase2_ary = [phrase2, normalize(phrase2)]
    for p1 in phrase1_ary:
        for p2 in phrase2_ary:
            if p1 and p2 and (p1 in p2 or p2 in p1):
                return True
    return False

def find_subordinate_verb_phrase(vp):
    rel_pro_indexes = [i for i, l in enumerate(vp.leaves()) if l == ('que', 'PRO-KS-REL',)]
    if not rel_pro_indexes:
        return None
    return [l for i, l in enumerate(vp.leaves()) if i > rel_pro_indexes[-1]]
        
def is_conjunctive_verb_phrase(vp_tokens):

    return [i for i, l in enumerate(vp_tokens) if l in [(',', ',',), ('e', 'KC')]]

def score_predicates(tokens_pred1, tokens_pred2):
    verbs_tokens1 = [t for t in get_non_stop_tokens(tokens_pred1) if t[1] == "V"]
    verbs_tokens2 = [t for t in get_non_stop_tokens(tokens_pred2) if t[1] == "V"]
    # is_subordinate(tokens_pred1)
    if len(verbs_tokens1) > 1:
        matches = 0
        for v1 in verbs_tokens1:
            has_match = False
            v1_phrases = [v1[0], normalize(v1[0])]
            v2_phrases = [v2[0] for v2 in verbs_tokens2]
            v2_phrases += [normalize(v) for v in v2_phrases]
            for v1p in v1_phrases:
                for v2p in v2_phrases:
                    if v1p in v2p or v2p in v1p:
                        has_match = True
                        break
            matches += int(has_match)
            

        return matches/len(verbs_tokens1)
    

    if "('não', 'ADV')" in str(tokens_pred1) and not "('não', 'ADV')" in str(tokens_pred2) or "('não', 'ADV')" not in str(tokens_pred1) and "('não', 'ADV')" in str(tokens_pred2):
        return 0
    #TODO correct to match the predicates and not return 100% of score
    return 1


def triple_score(t1, t2, domain_phrases):
    subject_phrase1 = "".join([normalize(get_domain_phrase(token[0], domain_phrases)) for token in get_non_stop_tokens(t1[0])])
    subject_phrase2 = "".join([normalize(get_domain_phrase(token[0], domain_phrases)) for token in get_non_stop_tokens(t2[0])])
    
    object_phrase1 = "".join([normalize(get_domain_phrase(token[0], domain_phrases)) for token in get_non_stop_tokens(t1[2])])
    
    
    object_phrase2 = "".join([normalize(get_domain_phrase(token[0], domain_phrases)) for token in get_non_stop_tokens(t2[2])])
    
    t1_sbj_phrs = [t[0] for t in t1[0] if "PHR" in t[0] ]
    t2_sbj_phrs = [t[0] for t in t2[0] if "PHR" in t[0] ]
    
    t1_obj_phrs = [t[0] for t in t1[2] if "PHR" in t[0] ]
    t2_obj_phrs = [t[0] for t in t2[2] if "PHR" in t[0] ]
    
    if max(len(t1_sbj_phrs), len(t2_sbj_phrs)):
        diff_count = len(set(t1_sbj_phrs) - set(t2_sbj_phrs)) + len(set(t2_sbj_phrs) - set(t1_sbj_phrs))
        if diff_count == max(len(t1_sbj_phrs), len(t2_sbj_phrs)):
            s_score = 0
        else:
            s_score = 1 - diff_count/10
    else:
        

        if has_intersection(subject_phrase1, subject_phrase2):
            s_score = 1
        else:
            if subject_phrase1 and subject_phrase1 == subject_phrase2:
                s_score = 1
            else:
                s_score = jaro_winkler_similarity(subject_phrase1, subject_phrase2)        
    
    
    if max(len(t1_obj_phrs), len(t2_obj_phrs)):
        diff_count = len(set(t1_obj_phrs) - set(t2_obj_phrs)) + len(set(t2_obj_phrs) - set(t1_obj_phrs))
        if diff_count == max(len(t1_obj_phrs), len(t2_obj_phrs)):
            o_score = 0
        else:
            o_score = 1 - diff_count/10
    else:
        

        if has_intersection(object_phrase1, object_phrase2):
            o_score = 1
        else:
            if object_phrase1 and object_phrase1 == object_phrase2:
                o_score = 1
            else:
                o_score = jaro_winkler_similarity(object_phrase1, object_phrase2)


    
    p_score = score_predicates(t1[1], t2[1])
    
    
    
    
    # import pdb; pdb.set_trace()
    if s_score < .85 or o_score < .85:
        return 0

    
    
    
    return (s_score +  p_score + o_score)/3

def infer_subjects(triples, tree, question_text, domain_phrases):
    triples_infered = [t.copy() for t in triples]
    
    question_text = preprocess(question_text)
    tokens = tokenize(question_text)
    question_phrase_matches = find_candidate_matches(tokens, domain_phrases)
    question_text_matched, match_dict = annotate_phrases(question_text, question_phrase_matches, domain_phrases)
    
    tagger = load_or_train_postagger()

    question_matched_tokens = tokenize(question_text_matched)
    pos_tagged = tagger.tag(question_matched_tokens)

    pos_tagged = [infer_class(tag) for tag in pos_tagged]

    parser = get_parser(get_grammar())
    tree = parser.parse(pos_tagged)
    
    sbj_candidates = [t for t in tree.subtrees() if t.label() in ["NER"]]
    if not sbj_candidates:
        sbj_candidates = [t for t in tree.subtrees() if t.label() in ["NP"]]
    
    for triple, cand in zip(triples_infered, sbj_candidates):
        if not triple[0]:

            triple[0] = cand.leaves()
    
    items_to_remove = []
    for i, triple in enumerate(triples_infered):
        if not triple[0]:
            if is_conjunctive_verb_phrase(triple[1]):
                if i >= 1:
                    triple[0] = triples_infered[i - 1][0]

            if i > 0 and triples_infered[i-1][0] and triples_infered[i-1][1] and triples_infered[i-1][2]:

                triple[0] = triples_infered[i-1][0]
# 
            if "PRO-KS-REL" in str(triples_infered[i - 1][2]):
                if i >= 1:
                    triple[0] = triples_infered[i - 1][0]

                    triples_infered[i-1][2].pop()
                    items_to_remove.append(triples_infered[i - 1])
            if "PREP" in str(triples_infered[i - 1][-1][-1]):
                if i >= 1:
                    triple[0] = triples_infered[i - 1][0]
                    items_to_remove.append(triples_infered[i - 1])
            
    
    for triple, cand in zip(triples_infered, sbj_candidates):
        if not triple[0]:

            triple[0] = cand.leaves()


    [triples_infered.remove(t) for t in items_to_remove]
 
    return triples_infered

def infer_predicates(triples, tree, question_text):
    return triples.copy()

def infer_objects(triples, tree, question_text):
    triples = triples.copy()
    for i, t in enumerate(triples):

        if i > 0 and t[-1] == "N" and not t[2]:
            t[2] = triples[i-1][2]

    return triples

def infer_missing_parts(triples, answer_tree, question_text, domain_phrases):
    triples_infered = triples.copy()
    
    triples_infered = infer_subjects(triples_infered, answer_tree, question_text, domain_phrases)
    triples_infered = infer_predicates(triples_infered, answer_tree, question_text)
    triples_infered = infer_objects(triples_infered, answer_tree, question_text)
    
    return triples_infered

def parse_free_verb_phrases(tree):
    ptree = ParentedTree.convert(tree)
    verb_phrases = [t for t in ptree.subtrees() if t.label() == "VP"]
    free_vps = [(v,i) for i, v in enumerate(verb_phrases) if not v.parent().label() == "STMT"]
    triples = []
    for free_vp, i in free_vps:
        if i > 0:
            preceding_vp = verb_phrases[i-1]
            parent = preceding_vp.parent()
            #TODO redundant code with parse_stmt(tree)
            if parent.label() == "STMT":
                subject_tokens = []
                predicate_tokens = []
                object_tokens = []
                
                complement_subtrees = [t for t in parent.subtrees() if t.label() == "CPL"]
                verb_phrase_subtrees = [t for t in parent.subtrees() if t.label() == "VP"]
                
                subject_candidate = [t for t in verb_phrase_subtrees[0].subtrees()][0]
                
                subject_tokens = extract_subject(subject_candidate)

                
                predicate_tokens += [leaf for leaf in free_vp.leaves() if "V" in leaf[1]]

                for cpl in complement_subtrees:
                    object_tokens += cpl.leaves()

                
                if subject_tokens or predicate_tokens or object_tokens:
                    triple = [subject_tokens, predicate_tokens, object_tokens]

                    triples.append(triple)
                
    return triples

def qualify_affirmative_negative_triple(triple):
    
    if len(triple) == 4:
        return triple
    qualifier = "A"
    if "('não', 'adv')" in str(triple).lower() or "não/adv" in str(triple).lower():
        qualifier = "N"

    return [triple[0], triple[1], triple[2], qualifier]

def extract_triples(text, grammar, domain_phrases=[]):
    ref_answer = preprocess(text)
    ref_tokens = tokenize(ref_answer)
    
    ref_domain_phrase_matches = find_candidate_matches(ref_tokens, domain_phrases, True)
    ref_answer_matched, ref_dict = annotate_phrases(ref_answer, ref_domain_phrase_matches, domain_phrases)
    tagger = load_or_train_postagger()
    ref_matched_tokens = tokenize(ref_answer_matched)
    pos_tagged_ref_tokens = tagger.tag(ref_matched_tokens)
    pos_tagged_ref_tokens = [infer_class(tag) for tag in pos_tagged_ref_tokens]
    parser = get_parser(grammar)
    ref_tree = parser.parse(pos_tagged_ref_tokens)
    print(ref_tree)
    ref_triples = parse_stmt(ref_tree)
    ref_triples += parse_free_verb_phrases(ref_tree)
    ref_triples = [qualify_affirmative_negative_triple(t) for t in ref_triples]
    infered_ref_triples = []
    infered_ref_triples = infer_missing_parts(ref_triples, ref_tree, "", domain_phrases)
    infered_ref_triples = [qualify_affirmative_negative_triple(t) for t in infered_ref_triples]
    
    return infered_ref_triples

def find_keywords(text):
    return re.findall("\[([^[]*)\]", text)

def score_spo(answer, ref_answers, question_text = "", domain_phrases=[]):
    
    max_score = 0
    diff_max_score = []
    
    for ref_answer in ref_answers:
        
        
        domain_phrases = find_keywords(ref_answer)
        ref_answer = ref_answer.replace("[", "").replace("]", "")
        infered_ref_triples = extract_triples(ref_answer, get_grammar(), domain_phrases)
        infered_answer_triples = extract_triples(answer, get_grammar(), domain_phrases)

        # diff_max_score =  infered_ref_triples
        difference = []
        score = 0
        t_score = 0
        for ref_triple in infered_ref_triples:
            for answer_triple in infered_answer_triples:
                
                t_score = triple_score(answer_triple, ref_triple, domain_phrases)
                
                if t_score >= .9:
                    score += 1
                    break
   
            if not t_score:

                subject = []
                for s in ref_triple[0]:
                    s_token = s[0]
                    if "PHR" in s_token:
                        s_token = get_domain_phrase(s_token, domain_phrases)
                    subject.append((s_token, s[1]))

                ref_triple[0] = subject
                diff_tokens = [get_domain_phrase(t[0], domain_phrases) for part in ref_triple[:-1] for t in part]
                
                difference.append(diff_tokens)

        if infered_ref_triples:
            if not score:
                final_score = 0
            else:
                final_score = 1  - (len(infered_ref_triples) - score)/10
            # import pdb;pdb.set_trace()
            if final_score > max_score:
                max_score = final_score
                diff_max_score = difference
        
    return (max_score * 10 ,diff_max_score)
    
    


def score_keywords(answer, keywords):
    
    # print("ANSWER: ", answer)
    # print("KEYWORDS: ", keywords)
    # print()
    keywords = set([k for k in keywords if not pd.isnull(k)])


    if pd.isnull(answer):
        return [0, []]
    answer = preprocess(answer, False)
    answer_tokens = remove_stop_tokens(tokenize(answer))
    processed_keywords = []
    alt_keywords = {}
    original_row = []
    

    for k in keywords:
        
        processed_keywords = [s.strip() for s in k.split("|")]
        

        t1 = " ".join(remove_stop_tokens(tokenize(processed_keywords[0])))
        if not t1: continue
        original_row.append(t1)        
        
        if not alt_keywords.get(t1, None):
            alt_keywords[t1] = []
        
        for t2 in processed_keywords[1:]:
            t2 = " ".join(remove_stop_tokens(tokenize(t2)))
            
            
            if not (t1 == t2 or t2 in alt_keywords[t1] ):
                alt_keywords[t1].append(t2)
            # if not (t1 == t2 or t1 in alt_keywords[t2] ):
                # alt_keywords[t2].append(t1)

    # import pdb;pdb.set_trace()
    matrix = []
    matrix.append(original_row)
    
    for k, alt in alt_keywords.items():
        
        for alt_k in alt:
            for row in matrix:
                new_row = row.copy()
                if (k in new_row):
                    new_row.remove(k)
                    new_row.append(alt_k)
                    matrix.append(new_row)
    
    
    max_score = -1
    max_explain = None
    infered_ref_triples = []
    for row in matrix:
        # import pdb; pdb.set_trace()
        answer_domain_phrase_matches = find_candidate_matches(answer_tokens, row)
        matched_phrases = set([a[1] for a in answer_domain_phrase_matches])
        infered_ref_triples = extract_triples(answer, get_grammar(), row) or infered_ref_triples
        print("Infered ref: ", infered_ref_triples)
        if not matched_phrases:
            score = 0
        else: 
            print("matched: ", matched_phrases)
            print("row: ", row)
            print("answer tokens: ", answer_tokens)
            
            score = (len(matched_phrases)/len(row))*10
        
        
        explain = [k for k in row if k not in matched_phrases]


        if score > max_score:
            max_score = score
            max_explain = explain

    if not max_score:
        max_explain = keywords
    
    if len(answer_tokens) <= len(keywords) and not infered_ref_triples:
        max_score = 0
        max_explain = "Você deve fornecer uma resposta completa abordando os conceitos! Verifique a digitação e a concordância verbal e gramatical da sua frase"
    # import pdb;pdb.set_trace()
    
    
    print(infered_ref_triples)

    return (max_score, max_explain)

    # answer_matched, answer_dict  = annotate_phrases(answer, answer_domain_phrase_matches)
    
#TODO corref analysis

def score(answer, ref_answers, question_text = "", domain_phrases=[], weight_keywords = 0.5):
    max_keywords_score = 0
    weight_spo= 1 - weight_keywords
    diff_max_keywords_score = []
    all_keywords = set()
    difference = []


    for ref_answer in ref_answers:
        keywords = find_keywords(ref_answer)
        all_keywords.update(keywords)

        score, difference = score_keywords(answer, keywords)
        # import pdb;pdb.set_trace()
        if score > max_keywords_score:
            max_keywords_score = score
            diff_max_keywords_score = difference
    
    spo_score, spo_diff = score_spo(answer, ref_answers, question_text)
    total_score = max_keywords_score * weight_keywords + spo_score * weight_spo
    
    if not max_keywords_score:
        diff_max_keywords_score = difference
    
    # import pdb;pdb.set_trace()
    total_diff = spo_diff + list(diff_max_keywords_score)
    # import pdb;pdb.set_trace()
    # 
    return (total_score, total_diff)
        




