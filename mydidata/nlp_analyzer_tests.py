from django.test import TestCase
from mydidata.nlp_operations import *

###
### to run specific test cases do: python manage.py test mydidata.nlp_analyzer_tests.TestNLPAnalizer.test_find_candidate_matches_synonyms
###
class TestNLPAnalizer(TestCase):
    def setUp(self):
        self.grammar = '''
        
          
            
            NER: {<ART>?<NE>}
            NP: {<ART>?(<N.*>)<ADJ>?<PCP>?}
            NP: {<ART>(<ADJ>|<PCP>)}
            VP: {<NP>?<ADV>?<ART>?<:>?<->?(<V>(<,>|<KC>)?)+}
            STPREP: {<NP><PREP><NP>}
            STPREP2: {<PREP>(<NP>(<,>|<KC>)?)+}
            CPL: {(<STPREP.*>|<PREP.*>|<N.*>|<NPROP>|<PCP>|<PRO-KS-REL>|<ADV>)*}
            
            STMT: {<VP>((<,>|<KC>)?<CPL> )*}
            
        
        '''
        self.test_sentences = [
            "A animal tem núcleo e a vegetal não.",
            "a célula vegetal tem parede celular a animal não",
            "uma tem núcleo e a outra não",
            "animal tem nucleo e a animal n tem nucleo",
            "Uma é de seres vivos a outra é de plantas,vegetais. \ uma tem parede celular a outra não.",
            "Que as células animais tem várias funções a mais do que as vegetais pois os animais falam andam tem um sistema digestivo complexo tem vários órgãos e os das plantas tem somente a fotossíntese,a criação de nutrientes,a absorção de água e etc.Por isso as células são diferentes pois as plantas são bem diferentes dos animais.",
            "A célula vegetal possui mais células que a animal e a animal é dos animais e vegetal das plantas e vegetais.",
        ]

        self.expected_triples = [
            [
                ["A célula animal", "tem", "núcleo", "A"],
                ["A célula vegetal", "tem", "núcleo", "N"]
            ],
            [],
            [],
            [],
            [],
        ]

    def test_extract_entities(self):
        expected_entities = [
            ('celul animal', 'celular animal', 3), ('animal nucle', 'animal núcleo', 2), 
            ('celul veget', 'célula vegetal', 2), ('veget pared', 'vegetal parede', 2), 
            ('pared celul', 'parede celular', 2), ('animal animal', 'animal animal', 2), 
            ('nucle veget', 'núcleo vegetal', 1), ('nucle outr', 'núcleo outra', 1), 
            ('nucle animal', 'nucleo animal', 1), ('animal n', 'animal n', 1), 
            ('ser viv', 'seres vivos', 1), ('viv outr', 'vivos outra', 1), 
            ('outr plant', 'outra plantas', 1), ('plant veget', 'plantas vegetais', 1), 
            ('celul outr', 'celular outra', 1), ('animal var', 'animais várias', 1), 
            ('var func', 'várias funções', 1), ('func veget', 'funções vegetais', 1), 
            ('veget poi', 'vegetais pois', 1), ('poi animal', 'pois animais', 1), 
            ('animal fal', 'animais falam', 1), ('fal and', 'falam andam', 1), 
            ('and sistem', 'andam sistema', 1), ('sistem diges', 'sistema digestivo', 1), 
            ('diges complex', 'digestivo complexo', 1), ('complex vari', 'complexo vários', 1),
             ('vari org', 'vários órgãos', 1), ('org plant', 'órgãos plantas', 1), 
             ('plant soment', 'plantas somente', 1), 
             ('soment fotossintes', 'somente fotossíntese', 1), 
             ('fotossintes cri', 'fotossíntese criação', 1), ('cri nutri', 'criação nutrientes', 1), 
             ('nutri absorc', 'nutrientes absorção', 1), ('absorc agu', 'absorção água', 1), 
             ('agu etc.p', 'água etc.Por', 1), ('etc.p celul', 'etc.Por células', 1), 
             ('celul sao', 'células são', 1), ('sao difer', 'são diferentes', 1), 
             ('difer poi', 'diferentes pois', 1), ('poi plant', 'pois plantas', 1), 
             ('plant sao', 'plantas são', 1), ('sao bem', 'são bem', 1), 
             ('bem difer', 'bem diferentes', 1), ('veget possu', 'vegetal possui', 1), 
             ('possu celul', 'possui células', 1), ('animal veget', 'animais vegetal', 1), 
             ('veget plant', 'vegetal plantas', 1)]


        
        entities = extract_entities(self.test_sentences)

        self.assertEquals(entities, expected_entities)

    def test_extract_bigrams(self):
        expected_entities = [
            ('animal', 'animal', 11), ('veget', 'vegetal', 8), ('celul', 'célula', 8), 
            ('nucle', 'núcleo', 5), ('plant', 'plantas', 5), ('outr', 'outra', 4), 
            ('a', 'A', 3), ('pared', 'parede', 3), ('poi', 'pois', 3), 
            ('difer', 'diferentes', 3), ('n', 'n', 2), ('uma', 'Uma', 2), 
            ('ser', 'seres', 2), ('viv', 'vivos', 2), ('que', 'Que', 2), 
            ('var', 'várias', 2), ('func', 'funções', 2), ('fal', 'falam', 2), 
            ('and', 'andam', 2), ('sistem', 'sistema', 2), ('diges', 'digestivo', 2), 
            ('complex', 'complexo', 2), ('vari', 'vários', 2), ('org', 'órgãos', 2), 
            ('soment', 'somente', 2), ('fotossintes', 'fotossíntese', 2), 
            ('cri', 'criação', 2), ('nutri', 'nutrientes', 2), ('absorc', 'absorção', 2), 
            ('agu', 'água', 2), ('etc.p', 'etc.Por', 2), ('bem', 'bem', 2), 
            ('possu', 'possui', 2)
        ]


        entities = extract_bigram_entities(self.test_sentences)
        print(entities)
        self.assertEquals(entities, expected_entities)







    def test_tokenize(self):
        text = "A célula animal é eucarionte e heterotrófica."
        tokens = tokenize(text)
        expected_results = ["A", "célula", "animal", "é", "eucarionte", "e", "heterotrófica", "."]
        self.assertEqual(tokens, expected_results)
    
    def test_sentece_tokenize(self):
        text = "A célula animal é eucarionte e heterotrófica. Os vegetais são seres autotróficos e procariontes."
        expected_results = set([
            "A célula animal é eucarionte e heterotrófica.",
            "Os vegetais são seres autotróficos e procariontes."
        ])
        self.assertEqual(set(sentence_tokenize(text)), expected_results)
    
    def test_normalize(self):
        self.assertEqual("celul", normalize("célula"))
        self.assertEqual("procariont", normalize("Procarionte"))

    def test_find_candidate_matches_three_words(self):
        tokens = ["A", "célula", "animal", "é", "eucarionte", "e", "heterotrófica", "."]
        expected_results = [(['eucarionte', 'e', 'heterotrófica'], 'eucarionte e heterotrófica', (4, 6))]
        keywords = ["eucarionte e heterotrófica"]
        self.assertListEqual(find_candidate_matches(tokens, keywords), expected_results)

    def test_find_candidate_matches(self):
        tokens = ["A", "célula", "animal", "é", "eucarionte", "e", "heterotrófica", "."]
        keywords = ["célula animal", "eucarionte", "heterotrófica"]
        expected_results = [
            (['célula', 'animal'], 'célula animal', (1, 2)),
            (['eucarionte'], 'eucarionte', (4, 4)),
            (['heterotrófica'], 'heterotrófica', (6, 6)),
        ]
        actual_results = find_candidate_matches(tokens, keywords)
        print("CAND MATCHES: ", actual_results)
        self.assertListEqual(actual_results, expected_results)

    def test_find_candidate_matches_synonyms(self):
        tokens = ["na", "célula", "das", "plantas", "há", "cloroplasto", "parede", "celular", "de", "celulose", "e", "vacuolo", "pulsatil"]
        keywords = ["célula vegetal"]
        expected_results = [
            (['célula', 'das', 'plantas'], 'célula vegetal', (1, 3)),
        ]

        self.assertListEqual(find_candidate_matches(tokens, keywords), expected_results)
    
    def test_find_candidate_matches_synonyms_2(self):
        tokens = ["na", "célula", "vegetal", "há", "cloroplasto", "parede", "celular", "de", "celulose", "e", "vacuolo", "pulsatil"]
        keywords = ["célula das plantas"]
        expected_results = [
            (['célula', 'vegetal'], 'célula das plantas', (1, 2)),
        ]

        self.assertListEqual(find_candidate_matches(tokens, keywords), expected_results)

    def test_find_candidate_matches_typos(self):
        tokens = ["A", "célula", "animal", "é", "eucarionte", "e", "heterotrófica", "."]
        expected_results = [(['eucarionte', 'e', 'heterotrófica'], 'ecuarinte e eterotrofica', (4, 6))]
        keywords = ["ecuarinte e eterotrofica"]
        self.assertListEqual(find_candidate_matches(tokens, keywords), expected_results)

    def test_annotate_phrases(self):
        matches = [
            (['célula', 'animal'], 'célula animal', (1, 2)),
            (['eucarionte'], 'eucarionte', (4, 4)),
            (['heterotrófica'], 'heterotrófica', (6, 6)),
        ]
        keywords = ["célula animal", "eucarionte", "heterotrófica"]
        text = "A célula animal é eucarionte e heterotrófica."
        text_annotated, entity_map = annotate_phrases(text, matches, keywords)
        expected_entity_map = {
            "PHR0": ['célula', 'animal'], 
            "PHR1": ["eucarionte"], 
            "PHR2": ["heterotrófica"]
        }

        self.assertDictEqual(entity_map, expected_entity_map)
        self.assertEqual(text_annotated, "A PHR0  é PHR1  e PHR2 .")
    
    def test_find_candidates_incomplete_keywords(self):
        tokens = ["A", "animal", "é", "eucarionte", "e", "heterotrófica", "."]
        expected_results = [(['A', 'animal'], 'célula animal', (0, 1))]
        keywords = ["célula animal"]
        self.assertListEqual(find_candidate_matches(tokens, keywords, search_corref=True), expected_results)
    
    def test_parse_stmt(self):
        pos_tagged1 = [
            ('PHR1', "NE"), 
            ('tem', 'V'), 
            ('PHR3', "NE"), 
            ('e', 'KC'), 
            ('PHR4', "NE"), 
            (',', ','), 
            ('a', 'ART'), 
            ('PHR0', "NE"), 
            ('não', 'ADV'), 
            ('tem', 'V'), 
            ('.', '.')
        ]

        pos_tagged2 = [
            ('PHR1', "NE"), 
            ('não', 'ADV'), 
            ('tem', 'V'), 
            ('PHR4', "NE"), 
            ('e', 'KC'), 
            ('PHR3', "NE"), 
            (',', ','), 
            ('a', 'ART'), 
            ('PHR0', "NE"), 
            ('não', 'ADV'), 
            ('tem', 'V'), 
            ('.', '.')
        ]

        pos_tagged3 = [
            ('A', 'ART'), 
            ('PHR0', 'NE'), 
            ('é', 'V'), 
            ('PHR1', "NE"), 
            (',', ','), 
            ('PHR2', "NE"), 
            (',', ','), 
            ('já', 'ADV'), 
            ('os', 'ART'), 
            ('vegetais', 'ADJ'), 
            ('são', 'V'), ('seres', 'N'), 
            ('autotróficos', "N"), 
            ('e', 'KC'), 
            ('procariontes', "N")
        ]
        expected_stmts = '''
            (STMT
                (VP (NP (NER PHR1/NE)) tem/V)
                (CPL (NP (NER PHR3/NE)))
                e/KC
                (CPL (NP (NER PHR4/NE))))
            ,/,
            (STMT (VP (NP (NER a/ART PHR0/NE)) não/ADV tem/V))
        '''

        parser = nltk.RegexpParser(self.grammar)
        tree = parser.parse(pos_tagged1)
        
        self.assertTrue(expected_stmts.replace(" ", "").replace("\n", "") in str(tree).replace(" ", "").replace("\n", ""))
        
        tree = parser.parse(pos_tagged2)
        expected_stmts = '''
        (STMT
            (VP (NP (NER PHR1/NE)) não/ADV tem/V)
            (CPL (NP (NER PHR4/NE)))
            e/KC
            (CPL (NP (NER PHR3/NE))))
        ,/,
        (STMT (VP (NP (NER a/ART PHR0/NE)) não/ADV tem/V))
        '''
        self.assertTrue(expected_stmts.replace(" ", "").replace("\n", "") in str(tree).replace(" ", "").replace("\n", ""))
        
        tree = parser.parse(pos_tagged3)
        expected_stmts = '''
        (STMT
            (VP (NP (NER A/ART PHR0/NE)) é/V)
            (CPL (NP (NER PHR1/NE)))
            ,/,
            (CPL (NP (NER PHR2/NE)))
        '''
        expected_stmts2 = '''
         (STMT
            (VP (NP os/ART vegetais/ADJ) são/V)
            (CPL (NP seres/N) (NP autotróficos/N))
            e/KC
            (CPL (NP procariontes/N))))

        '''
        self.assertTrue(expected_stmts.replace(" ", "").replace("\n", "") in str(tree).replace(" ", "").replace("\n", ""))
        self.assertTrue(expected_stmts2.replace(" ", "").replace("\n", "") in str(tree).replace(" ", "").replace("\n", ""))

    def test_parse_stmt_neg_sentence(self):
        expected_output = '''
        (S
            (STMT 
                (VP (NP (NER PHR0/NE)) tem/V) (CPL (NP (NER PHR2/NE))))
            (STMT (VP (NP (NER a/ART PHR1/NE)) não/ADV tem/V))
        ./.)
        '''
        pos_tagged = [
            ('PHR0', "NE"), 
            ('tem', 'V'), 
            ('PHR2', "NE"), 
            ('a', 'ART'), 
            ('PHR1', "NE"), 
            ('não', 'ADV'), 
            ('tem', 'V'), 
            ('.', '.')
        ]
        parser = nltk.RegexpParser(self.grammar)
        tree = parser.parse(pos_tagged)
        self.assertEqual(expected_output.replace(" ", "").replace("\n", ""), str(tree).replace(" ", "").replace("\n", ""))


    # def test_parse_tree_stc_que(self):
    #     self.fail()

    def test_extract_triples1(self):
        parsed_tree = '''
        (S
            (STMT 
                (VP (NP (NER PHR1/NE)) não/ADV tem/V)
                (CPL (NP (NER PHR4/NE)))
                e/KC
                (CPL (NP (NER PHR3/NE)))
            )
            (. .))
        '''
        expected_results = [
            [
                [("PHR1", "NE")],
                [("não", "ADV"), ("tem", "V")],
                [("PHR4", "NE"), ("PHR3", "NE")]
            ]
        ]
        leaf_parse = lambda leaf_str: tuple(leaf_str.split("/"))
        tree = Tree.fromstring(parsed_tree, read_leaf=leaf_parse)
        triples = parse_stmt(tree)
        self.assertListEqual(triples, expected_results)
        

    def test_extract_triples2(self):
        parsed_tree = '''
        (S
            (STMT
                (VP (NP (NER PHR0/NE)) é/V)
                (CPL (NP (NER PHR1/NE)))
                e/KC
                (CPL (NP (NER PHR2/NE))))
            ./.)
        '''
        expected_results = [
            [
                [("PHR0", "NE")],
                [("é", "V")],
                [("PHR1", "NE"), ("PHR2", "NE")]
            ]
        ]
        leaf_parse = lambda leaf_str: tuple(leaf_str.split("/"))
        tree = Tree.fromstring(parsed_tree, read_leaf=leaf_parse)
        triples = parse_stmt(tree)
        self.assertListEqual(triples, expected_results)


    def test_integration_1(self):
        text = "célula animal é eucarionte e heterotrófica."
        expected_results = [
            [
                [("PHR0", "NE")],
                [("é", "V")],
                [("PHR1", "NE"), ("PHR2", "NE")],
                "A"
            ]
        ]
        keywords = ["célula animal", "eucarionte", "heterotrófica"]
        
        triples = extract_triples(text, self.grammar, keywords)
        self.assertListEqual(triples, expected_results)
        
    def test_integration_neg_first_triple(self):
        text = "célula vegetal tem cloroplasto a célula animal não tem ."
        expected_results = [
            [
                [('PHR0', 'NE')], 
                [('tem', 'V')], 
                [('PHR2', 'NE')],
                'A'
            ], 
            [
                [('a', 'ART'), ('PHR1', 'NE')], 
                [('não', 'ADV'), ('tem', 'V')], 
                [('PHR2', 'NE')], 
                'N'
            ]
        ]
        keywords = ["célula vegetal", "célula animal", "cloroplasto", "heterotrófica"]
        
        triples = extract_triples(text, self.grammar, keywords)
        # print("TRIPLES: ", triples)
        self.assertListEqual(triples, expected_results)

    def test_integration_composite_vps(self):
        text = "a função do fígado é filtrar o sangue e eliminar toxinas."
        expected_results = [
            [
                [('fígado', 'N')], 
                [('é', 'V'), ('filtrar', 'V')], 
                [('o', 'ART'), ("sangue", 'N')], 
                'A'
            ],
            [
                [('fígado', 'N')], 
                [('eliminar', 'V')], 
                [("toxinas", 'N')], 
                'A'
            ]

        ]
        
        
        triples = extract_triples(text, self.grammar)
        # print("TRIPLES: ", triples) 
        # import pdb;pdb.set_trace()
        self.assertListEqual(triples, expected_results)
    
    def test_integration_relative_prn_sentece(self):
        text = "Hosts são dispositivos que não possuem endereços de Internet"
        expected_results = [
            [
                [('Hosts', 'N')], 
                [('não', 'ADV'), ('possuem', 'V')], 
                [('endereços', 'N'), ('Internet', 'NPROP')], 
                'N'
            ]

        ]
        
        
        triples = extract_triples(text, self.grammar)
        # print("TRIPLES: ", triples)
        # import pdb;pdb.set_trace()
        self.assertListEqual(triples, expected_results)
    
    def test_extract_triples3(self):
        text = "A interconexão e o cabo horizontal que termina em um painel distribuidor chamado patch panel, que se conecta ai switch Ethernet.  A conecxão cruzada é um tecnica que exige dois patch panel ou um bloco com duas fileras de parte"
        ref_answers = [
            "O cabeamento horizontal faz liga a área de trabalho e a sala de telecomunicações.",
            "cabeamento horizontal faz a interface entre a sala de telecomunicações e a área de trabalho."
        ]
        triples = extract_triples(text, self.grammar)
        # print("TRIPLES: ", triples) 
    
    def test_extract_triples_start_V(self):
        text = "É o estudo da interação entre os seres_vivos e o meio_ambiente."
        expected_triples = [
            [
                [], 
                [('É', 'V')], 
                [('estudo', 'N'), ('interação', 'N')],
                'A'
            ], 
            [
                [("seres_vivos", "N")],
                [("interação", "N")],
                [("meio_ambiente", "N")],
                "A"
            ]
        ]

        triples = extract_triples(text, self.grammar)
        # print("TRIPLES: ", triples) 
        self.assertListEqual(triples, expected_triples)

    def test_extract_triples_from_fixtures(self):
        
        
        actual_t = extract_triples(self.test_sentences[0], self.grammar)
        expected_triples = [
            [
                [('a', 'ART'), ('vegetal', 'ADJ')], 
                [('tem', 'V')], 
                [('núcleo', 'N')], 
                'N'
            ], 
            [
                [('A', 'ART'), ('animal', 'N')], 
                [('tem', 'V')], 
                [('núcleo', 'N')], 
                'A'
            ]
        ]

        self.assertListEqual(expected_triples, actual_t)

    def test_score_equal_answer_ref_answer(self):
        answer = "Hosts são dispositivos que não possuem endereços de Internet"
        reference_answers = ["Hosts são dispositivos que não possuem endereços de Internet"]
        self.assertTupleEqual(score_spo(answer, reference_answers), (10.0, []))
    
    def test_score_answer_ref_answer(self):
        answer = "Hosts possuem endereços de Internet"
        reference_answers = ["[Hosts] são dispositivos que têm endereços de Internet"]
        missing_triples = [

        ]
        self.assertTupleEqual(score_spo(answer, reference_answers), (10.0, missing_triples))
    
    def test_score3(self):
        answer = "A interconexão e o cabo horizontal que termina em um painel distribuidor chamado patch panel, que se conecta ai switch Ethernet.  A conecxão cruzada é um tecnica que exige dois patch panel ou um bloco com duas fileras de parte"
        reference_answers = [
            "O [cabeamento horizontal] liga a [área de trabalho] e a sala de telecomunicações.",
            "[cabeamento horizontal] faz a interface entre a sala de telecomunicações e a [área de trabalho]."
        ]
        self.assertTupleEqual(score_spo(answer, reference_answers), (0.0, []))

    def test_score_general1(self):
        answer = "O cabeamento horizontal liga a área de trabalho e a sala de telecomunicações."
        reference_answers = [
            "O [cabeamento horizontal] liga a [área de trabalho] e a sala de telecomunicações.",
            "[cabeamento horizontal] faz a interface entre a sala de telecomunicações e a [área de trabalho]."
        ]
        self.assertTupleEqual(score(answer, reference_answers), (10.0, []))

    def test_score_general2(self):
        answer = "O cabeamento horizontal liga a sala de equipamentos a sala de telecomunicações."
        
        reference_answers = [
            "O [cabeamento horizontal] liga a [área de trabalho] e a [sala de telecomunicações].",
            "[cabeamento horizontal] faz a interface entre a sala de telecomunicações e a [área de trabalho]."
        ]

        self.assertTupleEqual(score(answer, reference_answers, weight_keywords=0.3), (9.0, ['área trabalho']))
    def test_score_general3(self):
        answer = "Interconexão Vs. Conexão Cruzada   Os cabos horizontais terminam nos distribuidores e painéis do armário de telecom do andar. Entretanto, como podemos conectar os cabos horizontais ao switch ethernet de acesso do andar? Temos duas possibilidades, podemos utilizar um esquema mais simples, chamado interconexão ou um esquema um pouco mais caro e elaborado, que é a de conexão cruzada. Na interconexão, o cabo horizontal termina em um painel distribuidor chamado Patch Panel, que por sua vez, se conecta ao Switch Ethernet. Veja o esquema de interconexão abaixo."
        
        reference_answers = [
            "[interconexão] [cabo horizontal] [patch panel]."
            
        ]

        self.assertTupleEqual(score(answer, reference_answers), (5.0, []))
        
    def test_score_general4(self):

        answer = "na celula vegetal há cloroplasto, parede celular de celulose e vacuolo pulsatil"
        reference_answers = [
            "[vegetal] possui [cloroplastos]"
        ]
        expected_answer = (10.0,
        [])


        self.assertTupleEqual(score(answer, reference_answers), expected_answer)

    def test_score_general5(self):

        answer = "jogar suco gástrico o estômago para digerir a comida."
        reference_answers = [
            "a função do [fígado] é filtrar [toxinas]"
        ]
        expected_answer = (0.0,
        ['toxinas', 'fígado'])


        self.assertTupleEqual(score(answer, reference_answers), expected_answer)
    
    def test_score_time(self):
        import time

        test_sentences = [
            "a função do fígado é filtrar e eliminar toxinas.",
            "As diferenças entre elas são  a estrutura , formato , e componentes que constitui a célula!",
            "célula vegetal tem cloroplasto célula animal não tem .",
            "A célula animal, é eucarionte, heterotrófica, já os vegetais são seres autotróficos e procariontes",
            "A vegetal é Procarionte (não possui carioteca) e a animal é Eucarionte (possúi carioteca).",
            "A célula animal são as células dos animais e são adeptos para os animais e a célula vegetal é as células para os vegetais.",
            "a função é fomentar e inspecionar a orla.",
        ]
        reference_answers = [
            "a função do [fígado] é filtrar [toxinas]",
            "célula vegetal tem cloroplasto célula animal não tem"
        ]
        
        start_time = time.time()
        for s in test_sentences:
            score_keywords(s, reference_answers)
        print("--- %s seconds ---" % (time.time() - start_time))
    
    def test_erro_keyword_score(self):
        answer = "c) Controle de vetores de doenças crônicas;"
        reference_answers = [
            "Controle de vetores de doenças crônicas"
        ]
        expected_answer = (10.0,
        [])
        self.assertTupleEqual(score_keywords(answer, reference_answers), expected_answer)

    def test_error_pro_rel(self):
        answer = '''
            A política dos 3R's ( Reduzir, Reutilizar, Reciclar) é um conjunto de ações sugeridas durante a Conferência da Terra em 1992.

            Reduzir – Considerado o mais importante, refere a quantidade de lixo gerado que deve ser minimizada ao máximo. A redução é obtida através da aquisição de produtos mais resistentes que apresentem maior durabilidade, evitando ao máximo os produtos descartáveis. Algumas ações que contribuem para a redução da produção de lixo são: optar por guardanapos de pano em vez de papel, evitar usar sacolas de plástico, não desperdiçar alimentos, entre tantos outros. Fazer o necessário para reduzir a produção de novos produtos, contribuindo com os recursos naturais.

            Reutilizar – consiste no ato de, quando possível, utilizar várias vezes um determinado produto. Devemos priorizar as embalagens retornáveis e não as descartáveis. Com criatividade, novas funções podem ser dadas a objetos que iriam para o lixo, é o caso de latas, que podem ser transformadas em porta-lápis. Revistas, jornais, livros, entre outros materiais de leitura, dever ser doados em escolas e creches. Deve-se pensar nas possíveis utilizações de cada objeto antes de descartá-los.

            Reciclar: essa é a última etapa da política dos 3R’s, não sendo possível a reutilização de um objeto, a reciclagem é a melhor providência a ser tomada. Consiste na transformação dos resíduos em novos produtos ou matérias-primas. A coleta seletiva proporcionará a separação de produtos passíveis de reciclagem. Materiais como o alumínio, papel, plástico, vidro, entre outros, devem ser reciclados, contribuindo com os recursos naturais, pois a sua reciclagem evitará que novas matérias-primas sejam extraídas da natureza para a produção de determinados produtos.
        '''
        reference_answers = [
            "[Reduzir], [Reutilizar] e [Reciclar]"
        ]
        try:
            score(answer, reference_answers)
        except:
            self.fail()



test_sentences = [
    "a função do fígado é filtrar e eliminar toxinas.",
    "As diferenças entre elas são  a estrutura , formato , e componentes que constitui a célula!",
    "célula vegetal tem cloroplasto célula animal não tem .",
    "A célula animal, é eucarionte, heterotrófica, já os vegetais são seres autotróficos e procariontes",
    "A vegetal é Procarionte (não possui carioteca) e a animal é Eucarionte (possúi carioteca).",
    "A célula animal são as células dos animais e são adeptos para os animais e a célula vegetal é as células para os vegetais.",
    "a função é fomentar e inspecionar a orla.",
    """Cabo UTP (Unshielded Twisted Pair)

Cabo FTP (Foiled Twisted Pair)

Cabo SFTP (Screened Foiled Twisted Pair)

diferença entre eles o CABO UTP,além da malha de proteção que reveste todos os pares, possui um revestimento metálico para cada um dos pares, individualmente.

O CABO CABO FTP, Possui 4 pares de fios trançados, uma fibra para auxiliar na tração e um revestimento externo.

O CABO SFTP, Esse tipo de cabo, além da malha de proteção que reveste todos os pares, possui um revestimento metálico para cada um dos pares, individualmente.
""",
]

reference_answers = [
    "A célula animal é eucarionte, heterotrófica, já os vegetais são seres autotróficos e procariontes",
    "Hosts são dispositivos que não possuem endereços de Internet, sendo capazes de se comunicarem através da rede",
]

if __name__=="__main__":
    unittest.main()