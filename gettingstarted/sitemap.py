from django.contrib.sitemaps import Sitemap
from mydidata.models import Topic
class MySiteSitemap(Sitemap):
    changfreq = 'always'

    def items(self):
        return Topic.objects.filter(enabled=True)

    def lastmod(self, item):
        if(item.updated):
            return item.updated 
        
        return item.publish_date