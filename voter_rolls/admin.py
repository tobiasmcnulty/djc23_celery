from django.contrib import admin

from .models import PollingCenter, Voter, VoterRegistration

admin.site.register(PollingCenter)
admin.site.register(VoterRegistration)
admin.site.register(Voter)
