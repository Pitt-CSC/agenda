import os
import urllib
import datetime
import string
import calendar
import roleinfo

from google.appengine.ext import ndb

import jinja2
import webapp2

#If you want to debug, uncomment the line below and stick it wherever you want to break
#import pdb; pdb.set_trace();

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
    
    #Grab every role associated with a meeting
    @staticmethod
    def getAllRoles(agendaName):
        key = ndb.Key('Agenda', agendaName)
        roles_query = Role.query(ancestor=Agenda.gen_key(agendaName))
        return roles_query.fetch()

class Agenda(ndb.Model):
    """Models an agenda for one meeting."""        
    date = ndb.DateProperty()
    name = ndb.StringProperty()

    # Create a speaker role and attach it to this agenda
    def addDefaultSpeaker(self):
        speaker = Role(parent=self.gen_key(self.name), description=roleinfo.speakerDescription, notes = roleinfo.speakerNotes, minutes = roleinfo.speakerMinutes, presenter = roleinfo.presenterName)
        speaker.put()

    #Given a name, generate a key for an agenda
    @staticmethod
    def gen_key(agendaName):
        return ndb.Key('Agenda',agendaName)

    #Grab all coming agendas in order from soonest to farthest in the future
    @staticmethod
    def getQuery():
        return Agenda.query().order(-Agenda.date)

    #Return a list of every agenda
    @staticmethod
    def getAll():
        agendas_query =  Agenda.getQuery()
        return agendas_query.fetch()
    
class MainPage(webapp2.RequestHandler):

    def get(self):
       
        #See if there is an error to display
        msg = self.request.get('errorMessage')

        #Grab a query with every agenda
        agendas = Agenda.getAll()

        #Prepare our data for JINJA templating
        template_values = {
            'agendas': agendas,
            'errorMessage': msg,
        }

        #Render the page
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))

class NewAgenda(webapp2.RequestHandler):

    def post(self):

        #If an agenda already exists on the requested date, reject creation
        dateAsListOfInts = [int(x) for x in self.request.get('meeting').split('-')]
        date = datetime.date(*dateAsListOfInts)
        name = "{0} {1}, {2}".format(calendar.month_name[dateAsListOfInts[1]], dateAsListOfInts[2], dateAsListOfInts[0])

        #import pdb; pdb.set_trace();
        #If an agenda already exists on the requested date, reject creation
        agendaQuery = Agenda.getQuery()
        for agenda in agendaQuery:
            if agenda.name == name:
                query_params = {'errorMessage': "A meeting already exists on that day."}
                self.redirect('/?' + urllib.urlencode(query_params))
                return

        #Create, initialize, and store new agenda
        newAgenda = Agenda(date=date,name=name)
        newAgenda.addDefaultSpeaker()
        newAgenda.put()

        #Redirect to the newly created agenda
        query_params = {'agenda_name': name}
        self.redirect('/displayagenda?' + urllib.urlencode(query_params))


class DisplayAgenda(webapp2.RequestHandler):

    def get(self):
        #Grab all of the roles associated with this agenda
        agendaName = self.request.get('agenda_name')
        roles = Role.getAllRoles(agendaName)

        #Prepare data for JINJA templating
        template_values = {'roles': roles, 'agenda_name': agendaName}

        #Render the page
        template = JINJA_ENVIRONMENT.get_template('agenda.html')
        self.response.write(template.render(template_values))

application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/newagenda', NewAgenda ),
    ('/displayagenda', DisplayAgenda)
], debug=True)