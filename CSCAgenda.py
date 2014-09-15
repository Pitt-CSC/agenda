import os
import urllib
import datetime
import string
import calendar
import roleinfo

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
    presenter = ndb.StringProperty()
    minutes = ndb.IntegerProperty()
    notes = ndb.StringProperty()
    
class Agenda(ndb.Model):
    """Models an agenda for one meeting."""        
    date = ndb.DateProperty()
    name = ndb.StringProperty()

    def addDefaultSpeaker(self):
        speaker = Role(parent=self.gen_key(self.name), description=roleinfo.speakerDescription, notes = roleinfo.speakerNotes, minutes = roleinfo.speakerMinutes, presenter = roleinfo.presenterName)
        speaker.put()

    @staticmethod
    def gen_key(agendaName):
        return ndb.Key('Agenda',agendaName)
    
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

        dateAsListOfInts = [int(x) for x in self.request.get('meeting').split('-')]
        date = datetime.date(*dateAsListOfInts)
        
        name = "{0} {1}, {2}".format(calendar.month_name[dateAsListOfInts[1]], dateAsListOfInts[2], dateAsListOfInts[0])

        agenda = Agenda(date=date,name=name)
        agenda.addDefaultSpeaker()
        agenda.put()

        query_params = {'agenda_name': name}
        self.redirect('/displayagenda?' + urllib.urlencode(query_params))


class DisplayAgenda(webapp2.RequestHandler):

    def get(self):
        agendaName = self.request.get('agenda_name')
        key = ndb.Key('Agenda', agendaName)

        #import pdb; pdb.set_trace();

        roles_query = Role.query(
            ancestor=Agenda.gen_key(agendaName))

        roles = roles_query.fetch(15)

        template_values = {'roles': roles, 'agenda_name': agendaName}

        template = JINJA_ENVIRONMENT.get_template('agenda.html')
        self.response.write(template.render(template_values))

application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/newagenda', NewAgenda ),
    ('/displayagenda', DisplayAgenda)
], debug=True)