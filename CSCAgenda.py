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
    title = ndb.StringProperty()
    notes = ndb.StringProperty()
    isClaimed = ndb.BooleanProperty()
    
    #Grab every role associated with a meeting
    @staticmethod
    def getAllRoles(agenda_name):
        return Role.query(ancestor=Agenda.gen_key(agenda_name))

    #Given names for an agenda and a role, generate a key for an agenda
    @staticmethod
    def gen_key(agenda_name,role_name):
        import pdb; pdb.set_trace();
        return ndb.Key('Agenda',agenda_name,'Role',role_name)

class Agenda(ndb.Model):
    """Models an agenda for one meeting."""        
    date = ndb.DateProperty()
    name = ndb.StringProperty()

    # Create a stackpointer role and attach it to this agenda
    def addDefaultStackPointer(self):
        stackpointer = Role(parent=Agenda.gen_key(self.name), 
        description=roleinfo.stackpointerDescription,  
        presenter = roleinfo.stackpointerName, 
        isClaimed = False,
        title = "Stack Pointer")
        
        stackpointer.put()

    # Create a speaker role and attach it to this agenda
    def addDefaultSpeaker(self, title="Speaker"):
        speaker = Role(parent=Agenda.gen_key(self.name), 
        description=roleinfo.speakerDescription, 
        notes = roleinfo.speakerNotes, 
        minutes = roleinfo.speakerMinutes, 
        presenter = roleinfo.presenterName, 
        isClaimed = False,
        title = title)
        
        speaker.put()

    #Given a name, generate a key for an agenda
    @staticmethod
    def gen_key(agenda_name):
        return ndb.Key('Agenda',agenda_name)

    #Grab all coming agendas in order from soonest to farthest in the future
    @staticmethod
    def getQuery():
        return Agenda.query().order(-Agenda.date)

    #Return a list of every agenda
    @staticmethod
    def getAll():
        agendas_query =  Agenda.getQuery()
        return agendas_query.fetch()

def renderAgenda(agenda_name,handler):
    #Grab all of the roles associated with this agenda
    roles = Role.getAllRoles(agenda_name)

    #Prepare data for JINJA templating
    template_values = {'roles': roles, 'agenda_name': agenda_name}

    #Render the page
    template = JINJA_ENVIRONMENT.get_template('agenda.html')
    handler.response.write(template.render(template_values))

    
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
        agenda_name = "{0} {1}, {2}".format(calendar.month_name[dateAsListOfInts[1]], dateAsListOfInts[2], dateAsListOfInts[0])

        #import pdb; pdb.set_trace();
        #If an agenda already exists on the requested date, reject creation
        agendaQuery = Agenda.getQuery()
        for agenda in agendaQuery:
            if agenda.name == agenda_name:
                query_params = {'errorMessage': "A meeting already exists on that day."}
                self.redirect('/?' + urllib.urlencode(query_params))
                return

        #Create, initialize, and store new agenda
        newAgenda = Agenda(key = Agenda.gen_key(agenda_name),date=date,name=agenda_name)
        newAgenda.addDefaultSpeaker()
        newAgenda.addDefaultStackPointer()
        newAgenda.put()

        renderAgenda(agenda_name,self)


class DisplayAgenda(webapp2.RequestHandler):

    def get(self):
        #Grab all of the roles associated with this agenda
        agenda_name = self.request.get('agenda_name')
        renderAgenda(agenda_name,self)


class EditAgenda(webapp2.RequestHandler):

    def post(self):
        #Grab the role we want to edit
        #import pdb; pdb.set_trace();
        agenda_name = self.request.get('agenda_name')
        role_being_edited = self.request.get('title')
        query = Role.getAllRoles(agenda_name).filter(Role.title == role_being_edited)

        #Temporary janky loop. Should be identifying one unique role
        for role in query:
            role.presenter = self.request.get('presenter')
            #Check if it is claimed
            claimed = self.request.get('isClaimed')
            if claimed == 'on':
                role.isClaimed = True
            else:
                role.isClaimed = False
            #Store the edits
            role.put()

        #Show the edited agenda
        renderAgenda(agenda_name, self)


application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/newagenda', NewAgenda ),
    ('/displayagenda', DisplayAgenda),
    ('/edit', EditAgenda)
], debug=True)
