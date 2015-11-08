import sys,os,time,urllib2,json,traceback,jsonpickle
from ftplib import FTP
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
import selenium.webdriver.chrome.service as service

class HypothesisSelenium:

    def __init__(self, html_checklist=None, pdf_checklist=None, ext_path=None, out_path=None):
        self.host = 'hypothes.is'
        self.ftp_host = '***'
        self.ftp_user = '***'
        self.ftp_pass = '***'
        self.html_checklist = html_checklist
        self.pdf_checklist = pdf_checklist
        self.timing = HypothesisSeleniumTiming()
        self.h_results = {}
        self.h_profiling = {}
        self.via_results = {}
        self.stream_results = {}
        self.api_results = {}
        self.exceptions = ''
        self.ext_path = ext_path if ext_path is not None else ''
        self.out_path = out_path if out_path is not None else '.'
        self.history_path = '%s/history' % self.out_path
        self.json_diff_file = '%s/jsondiff_page.html' % self.out_path
        self.driver = None
        self.drivername = None
        self.wait_for_page_load = self.wait_for_page_load_html
        self.current_url = None
        self.timestamp = datetime.now().isoformat()[0:16].replace('-','').replace(':','')

    def get_timing(self):
        return self.timing.__dict__

    def wait_for_class(self,klass):
        return WebDriverWait(self.driver, self.timing.wait_for_klass_secs).until(
            EC.presence_of_element_located((By.CLASS_NAME, klass)))

    def wait_for_h_sidebar(self):
        WebDriverWait(self.driver,self.timing.wait_for_sidebar_frame_secs).until(
            EC.frame_to_be_available_and_switch_to_it((By.NAME,'hyp_sidebar_frame')))

    def wait_for_sidebar_to_fill(self):
         WebDriverWait(self.driver, self.timing.wait_for_sidebar_fill_secs).until(
            annotations_loaded(self))

    def wait_for_page_load_html(self):
        WebDriverWait(self.driver, self.timing.wait_for_page_load_secs).until(
            ready_state_is_complete())

    def wait_for_page_load_pdf(self):
        self.driver.switch_to_default_content()
        WebDriverWait(self.driver, self.timing.wait_for_page_load_secs).until(
            EC.presence_of_element_located((By.ID, 'pageContainer1')))
        self.driver.switch_to_frame('hyp_sidebar_frame')

    def open_page_with_h(self,url):
        self.driver.get(url)
        time.sleep(5)
        chevron = self.wait_for_class('h-icon-chevron-left')
        try:
            chevron.click()
        except:
            pass  # todo: throw exc
    
    def make_via_url(self,url):
        return 'https://via.hypothes.is/' + url

    def count_things(self):
        self.wait_for_h_sidebar()
        self.wait_for_page_load() 
        try:
            self.wait_for_sidebar_to_fill()
        except:
            self.exceptions += '<p>timeout waiting for sidebar fill for ' + self.current_url + '\n</p>'
        sidebar_annotation_count = len(self.driver.find_elements_by_class_name('annotation'))
        self.driver.switch_to_default_content()
        highlight_count = len(self.driver.find_elements_by_class_name('annotator-hl'))
        annotator_frame = self.driver.find_element_by_class_name('annotator-frame').text
        bucket_counts = ','.join(str(annotator_frame).split('\n'))
        return HypothesisSeleniumResult(sidebar_annotation_count, highlight_count, bucket_counts)  

    def check_url(self,url):
        try:
            start = datetime.now()
            self.h_results[url] = HypothesisSeleniumResult(-1,-1,-1)
            self.open_page_with_h(url)
            self.h_results[url] = self.count_things()
        except:
            self.exceptions += '<div>E) ' + url + ': ' + traceback.format_exc() + '</div>\n</p>'
        finally:
            stop = datetime.now()
            elapsed = stop - start
            self.h_profiling[url] = elapsed.total_seconds()

    def check_via_url(self,url):
        try:
            self.via_results[url] = HypothesisSeleniumResult(-1,-1,-1)
            via_url = self.make_via_url(url)
            self.open_page_with_h(via_url)
            self.via_results[url] = self.count_things()
        except:
            self.exceptions += '<div>V) ' + url + ': ' + traceback.format_exc() + '</div>\n</p>'
    
    def make_api_url(self,url):
        return 'https://%s/api/search?uri=%s' % (self.host, urllib2.quote(url))

    def check_api(self,url):
        self.api_results[url] = HypothesisSeleniumResult(-1,-1,-1)
        api_url = self.make_api_url(url)
        s = urllib2.urlopen(api_url).read()
        j = json.loads(s)
        api_count = j['total']
        self.api_results[url] = HypothesisSeleniumResult(api_count)
        
    def make_stream_url(self,url):
         return 'https://%s/stream?q=uri:%s' % (self.host, urllib2.quote(url))

    def check_stream(self,url):
        self.stream_results[url] = HypothesisSeleniumResult(-1,-1,-1)
        stream_url = self.make_stream_url(url)  
        self.driver.get(stream_url)
        self.wait_for_page_load()
        time.sleep(self.timing.wait_for_stream_load_secs)
        actions = webdriver.ActionChains(self.driver)
        actions.key_down(Keys.CONTROL).send_keys(Keys.END).perform() # broken in chrome driver, does nada
        stream_count = len(self.driver.find_elements_by_class_name('annotation'))
        self.stream_results[url] = HypothesisSeleniumResult(stream_count)
    
    def format_results(self):
        template = """<p><b>Annotations Found (%s)</b></p>
<p style="font-size:smaller">E: Extension, V: Via, S: Stream, A: API:, AC: Annotation Count, HL: Highlight Count, BC: Bucket Counts</p>
%s
<p><b>Exceptions</b></p>
%s"""
        s = ''
        for url in self.html_checklist + self.pdf_checklist:
            s += '<p>%s</p>\n' % url
            if self.h_results.has_key(url):
                r = self.h_results[url]
                elapsed = -1
                if self.h_profiling.has_key(url):
                    elapsed = self.h_profiling[url]
                s += '<div>E) AC %d, HL %d, BC %s (%.2f)</div>\n' % ( r.annotation_count, r.highlight_count, r.bucket_counts, elapsed )  
            else:
                s += '<div>E)</div>' 
            if self.via_results.has_key(url):
                r = self.via_results[url]
                s += '<div>V) AC %d, HL %d, BC %s</div>\n' % ( r.annotation_count, r.highlight_count, r.bucket_counts )   
            else:
                s += '<div>V)</div>' 
            if self.stream_results.has_key(url):
                r = self.stream_results[url]
                s += '<div>S) AC %d</div>\n' % ( r.annotation_count )
            else:
                s += '<div>S)</div>'
            if self.api_results.has_key(url):
                r = self.api_results[url]
                s += '<div>A) AC %d</div>\n' % ( r.annotation_count )  
            else:
                s += '<div>A)</div>'
            s += '</p>\n'
        return template % (self.ext_path, s, self.exceptions)

    def save_pickle(self, name):
        f = open(name, 'w')
        f.write(jsonpickle.encode(self))
        f.close()

    def ftp_results_page(self):
        ftp = FTP(self.ftp_host, self.ftp_user, self.ftp_pass)
        ftp.cwd('/public_html/h/selenium/history')
        fname = '%s-%s.html' % ( self.drivername, self.timestamp)
        f = open('%s/history/%s' % ( self.out_path, fname) )
        ftp.storbinary('STOR %s' % fname, f)
        f.close()

    def ftp_diff_page(self):
        ftp = FTP(self.ftp_host, self.ftp_user, self.ftp_pass)
        ftp.cwd('/public_html/h/selenium')
        f = open('report.html')
        ftp.storbinary('STOR report.html', f)
        f.close()

    def pickle(self):
        name = '%s/history/%s-%s.pickle' % ( self.out_path, self.drivername, self.timestamp)
        self.current_url = None        # remove clutter (it's a one-way trip)
        self.html_checklist = None
        self.pdf_checklist = None
        self.timing = None
        self.ftp_pass = None
        self.ftp_user = None
        self.ftp_host = None
        self.save_pickle(name)

    def write_results_page(self):
        html = """<html>
<head>
 <style>
   body { font-family:verdana; margin-left:.5in }
  div { margin-left: .5in }
  </style>
</head>
<body>
%s
</body>
</html>""" % self.format_results()
        f = open('%s/history/%s-%s.html' % ( self.out_path, self.drivername, self.timestamp), 'w')
        f.write(html)
        f.close()

    def apply_lenses(self, url, browser, type=None):
        self.current_url = url

        if ( type=='pdf'): 
            self.wait_for_page_load = self.wait_for_page_load_pdf
        else:
            self.wait_for_page_load = self.wait_for_page_load_html

        # api
        self.check_api(url)

        # stream
        """
        self.stream_results[url] = HypothesisSeleniumResult(-1)
        if ( type != 'pdf' ):
            self.driver = HypothesisSeleniumDriver(browser).driver
            self.check_stream(url)
            self.driver.quit()
        """

        # via
        self.driver = HypothesisSeleniumDriver(browser).driver
        self.drivername = self.driver.name
        self.check_via_url(url)
        self.driver.quit()

        # extension

        self.driver = HypothesisSeleniumDriver(browser, self.ext_path).driver
        self.drivername = self.driver.name
        self.check_url(url)
        self.driver.quit()

        self.current_url = None
        self.driver = None

    def do_browser(self, browser):
        for url in self.pdf_checklist:
            self.apply_lenses(url, browser, 'pdf')
        for url in self.html_checklist:
            self.apply_lenses(url, browser)
        self.write_results_page()
        self.ftp_results_page()
        self.pickle()
        self.json_diff()

    def get_recent_pair_of_results(self, type):
        results = [f for f in os.listdir(self.history_path) if f.endswith(type)]
        results.sort()
        results = results[-2:]
        return results

    def get_historical_file(self,name):
        path = '%s/%s' % (self.history_path, name)
        return open(path).read()

    def get_historical_path(self,name):
        path = '%s/%s' % (self.history_path, name)
        return path
        
    def json_diff(self):
        files = os.listdir(self.out_path)
        pickles = self.get_recent_pair_of_results('pickle')
        htmls =   self.get_recent_pair_of_results('html')
        pickle_a = self.get_historical_file(pickles[0])
        pickle_b = self.get_historical_file(pickles[1])
        html_path_a = self.get_historical_path(htmls[0])
        html_path_b = self.get_historical_path(htmls[1])
        page = open(self.json_diff_file).read()
        page = page.replace('_A_HTML_', html_path_a)
        page = page.replace('_B_HTML_', html_path_b)
        page = page.replace('_A_JSON_', pickle_a)
        page = page.replace('_B_JSON_', pickle_b)
        f = open('report.html','w')
        f.write(page)
        f.close()
        self.ftp_diff_page()
        
class HypothesisSeleniumDriver():

    def __init__(self,browser,ext_path=None):
        self.ext_path = ext_path
        self.driver = None
        self.options = Options()

        if browser == 'firefox':
            self.driver = webdriver.Firefox()

        if browser == 'chrome':
            if self.ext_path is not None:
                self.options.add_extension(self.ext_path)
                self.options.add_experimental_option('excludeSwitches', ['test-type','ignore-certificate-errors']) # https://code.google.com/p/chromedriver/issues/detail?id=1081
            self.driver = webdriver.Chrome(chrome_options=self.options)

        if browser == 'ie':
            self.driver = webdriver.Ie()

        self.drivername = self.driver.name
        #self.driver.implicitly_wait(HypothesisSeleniumTiming().very_long_wait)
        self.driver.set_page_load_timeout(HypothesisSeleniumTiming().wait_for_page_load_secs)
        self.driver.set_script_timeout(HypothesisSeleniumTiming().wait_for_script_secs)

class HypothesisSeleniumResult():

     def __init__(self, annotation_count, highlight_count=None, bucket_counts=None):
         self.annotation_count = annotation_count
         self.highlight_count = highlight_count
         self.bucket_counts = bucket_counts

     def to_dict(self):
         dict = {
             'annotation_count': self.annotation_count,
             'highlight_count': self.highlight_count,
             'bucket_counts': self.bucket_counts
             }
         return dict

class HypothesisSeleniumTiming():

    def __init__(self):
        self.very_short_wait = 1
        self.short_wait = 5
        self.medium_wait = 15
        self.long_wait = 30
        self.very_long_wait = 90
        self.wait_for_sidebar_fill_secs =       self.long_wait
        self.wait_for_scroll_down_secs =        self.very_short_wait
        self.wait_for_sidebar_frame_secs =      self.short_wait
        self.wait_for_stream_load_secs =        self.medium_wait
        self.wait_for_pdf_pagecontainer_secs =  self.long_wait
        self.wait_for_script_secs =             self.long_wait
        self.wait_for_page_load_secs =          self.long_wait
        self.wait_for_klass_secs =              self.very_long_wait
                
class ready_state_is_complete(object):
    """ An expectation for checking whether document.readyState == 'complete'
    """
    def __init__(self):
        pass

    def __call__(self, driver):
        try:
            return driver.execute_script("return document.readyState") == 'complete'
        except:
            return False

class annotations_loaded(object):
    """ An expectation for checking if all annotations loaded
    """
    def __init__(self, hs):
        self.hs = hs
        self.count = hs.api_results[hs.current_url].annotation_count

    def __call__(self, driver):
        try:
            c = driver.execute_script("return $('.annotation').length")
            if c > self.count:
                self.hs.exceptions += '<p>annotations_loaded for %s: expected %d, found %d</p>\n' % ( self.hs.current_url, self.count, c)
            return c >= self.count
        except:
            return False

if __name__ == '__main__':

    pdf_checklist = (
'http://www.jceps.com/wp-content/uploads/PDFs/10-2-03.pdf',
'http://caseyboyle.net/sense/hawhee.pdf',
'http://blogs.law.harvard.edu/copyrightx/files/2014/01/Understanding-Judicial-Opinions.pdf',
'http://arxiv.org/pdf/1207.0580v1.pdf',
'http://cyber.law.harvard.edu/people/tfisher/IP/1991_Feist.pdf',
'http://faculty.georgetown.edu/irvinem/theory/Berners-Lee-HTTP-proposal.pdf',
'http://partners.adobe.com/public/developer/en/pdf/PDFReference16.pdf',
'http://users-cs.au.dk/danvy/the-ideal-mathematician.pdf',
'http://wiki.openoil.net/images/4/43/AR01_07-06-2013_05-05-13_FULL_LIST.pdf',
'http://www.americanbar.org/content/dam/aba/publications/supreme_court_preview/BriefsV4/13-983_pet_amcu_mbbfap.authcheckdam.pdf'
        )[0:10]

    html_checklist = (
'http://guides.rubyonrails.org/active_record_migrations.html',
'https://www.facebook.com/notes/990860537613477/',
'http://w2.vatican.va/content/francesco/en/encyclicals/documents/papa-francesco_20150524_enciclica-laudato-si.html',
'https://peerj.github.io/paper-now/',
'http://www.newyorker.com/magazine/2015/05/18/tomorrows-advance-man',
'http://www.nytimes.com/2015/01/17/science/earth/2014-was-hottest-year-on-record-surpassing-2010.html',
'http://www.wsj.com/articles/climate-science-is-not-settled-1411143565',
'http://www.theatlantic.com/technology/archive/2014/08/advertising-is-the-internets-original-sin/376041/',
'http://blogs.kqed.org/education/2015/04/24/what-is-the-value-of-a-high-school-diploma/', # in via: Uncaught TypeError: jQuery is not a function
'http://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.04.0104:entry=ajax-bio-1',
'http://boundary2.org/2015/04/15/a-darked-warped-reflection/#',
'http://tkbr.ccsp.sfu.ca/pub802/2015/03/publishing-needs-a-hero-just-like-in-the-movies/',
'http://www.folgerdigitaltexts.org/html/MND.html',
'http://angular-tips.com/blog/2014/02/introduction-to-unit-test-introduction/',
'http://annarborobserver.com/articles/mary_morgan_and_dave_askins_full_article.html',
'http://arstechnica.com/information-technology/2013/08/forget-post-pc-pervasive-computing-and-cloud-will-change-the-nature-of-it/',
'http://blog.peerlibrary.org/post/60965604596/two-thousand-years-ago-plato-wrote-the-collected#notes', # tests https://github.com/hypothesis/h/issues/1909
'http://chronicle.com/article/The-MLA-Tells-It-Like-It-Is/146983',
'http://de.wikipedia.org/wiki/Dialektische_Darstellungsmethode',
'http://onedio.com/haber/internetin-derin-sulari-sasirtici-yonleri-bilinmeyenleri-ile-deep-web-456498',
'http://onlinelibrary.wiley.com/doi/10.1002/wdev.107/full',
'http://stackoverflow.com/questions/21013165/how-to-display-a-div-on-mouse-over-using-jquery',
'http://techcrunch.com/2014/04/12/culture-eats-strategy-for-breakfast/?ncid=twittersocialshare',
'http://www.autostraddle.com/the-new-yorkers-skewed-history-of-trans-exclusionary-radical-feminism-ignores-actual-trans-women-247642/',
'http://www.economist.com/blogs/democracyinamerica/2015/04/mike-huckabee-and-2016',
'http://www.emule.com/poetry/?page=poem&poem=4329',
'http://www.infoworld.com/article/2886828/collaboration-software/github-for-the-rest-of-us.html', # 20 second ad
'http://www.plosone.org/article/info:doi/10.1371/journal.pone.0078188',
'http://www.youtube.com/watch?v=JQiLaKdzD0E',
'https://medium.com/@jedsundwall/how-do-we-stay-sane-57b4078974fb',
'https://www.facebook.com/WestEndFarmersMarketSantaRosa',
'http://www.georgianjournal.ge/politics/30550-abandon-ship-is-the-national-movement-no-longer-united.html',
#'http://eds.a.ebscohost.com/eds/pdfviewer/pdfviewer?sid=868e0f1a-8504-4eff-9edd-33406ff9edc6@sessionmgr4002&vid=2&hid=4213', # iframe
   )[0:15]

    # Chrome

    hs = HypothesisSelenium(html_checklist=html_checklist, pdf_checklist=pdf_checklist, ext_path='./0.7.13.crx')

    hs.do_browser('chrome')



