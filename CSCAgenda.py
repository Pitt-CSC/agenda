import os
import urllib
import datetime
import string
import calendar

from google.appengine.ext import ndb

import jinja2
import webapp2


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class Role(ndb.Model):
    """Models a role a member can fill in a meeting."""
    description = ndb.StringProperty()
    speaker = ndb.StringProperty()
    minutes = ndb.IntegerProperty()
    notes = ndb.StringProperty()
    
class Agenda(ndb.Model):
    """Models an agenda for one meeting."""        
    date = ndb.DateProperty()
    name = ndb.StringProperty()
    roles = ndb.StructuredProperty(Role, repeated=True)
    
class MainPage(webapp2.RequestHandler):

    def get(self):
       
        #Grab all coming agendas in order from soonest to farthest in the future
        agendas_query = Agenda.query().order(-Agenda.date) # > datetime.datetime.today)
        agendas = agendas_query.fetch()

        template_values = {
            'agendas': agendas,
        }

        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))

class NewAgenda(webapp2.RequestHandler):

    def post(self):

        #import pdb; pdb.set_trace();

        dateAsListOfInts = [int(x) for x in self.request.get('meeting').split('-')]
        date = datetime.date(*dateAsListOfInts)
        
        name = "{0} {1}, {2}".format(calendar.month_name[dateAsListOfInts[1]], dateAsListOfInts[2], dateAsListOfInts[0])

        agenda = Agenda(date=date,name=name)
        agenda.put()

        self.redirect('/')

application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/newagenda', NewAgenda ),
], debug=True)