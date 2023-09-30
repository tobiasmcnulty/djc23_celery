from django.db import models


class PollingCenter(models.Model):
    center_id = models.CharField(max_length=5)
    center_name = models.CharField(max_length=64)

    @property
    def station_ids(self):
        return list(
            StationAssignment.objects.filter(center=self)
            .values_list("station_id", flat=True)
            .distinct()
        )

    def __str__(self):
        return f"{self.center_name} ({self.center_id})"


class Voter(models.Model):
    voter_id = models.CharField(max_length=12)
    voter_name = models.CharField(max_length=64)

    def __str__(self):
        return f"{self.voter_name} ({self.voter_id})"


class VoterRegistration(models.Model):
    voter = models.ForeignKey(Voter, on_delete=models.CASCADE)
    center = models.ForeignKey(PollingCenter, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.voter.voter_name}, registered at {self.center.center_name}"


class StationAssignment(models.Model):
    voter = models.ForeignKey(Voter, on_delete=models.CASCADE)
    center = models.ForeignKey(PollingCenter, on_delete=models.CASCADE)
    station_id = models.IntegerField()

    def __str__(self):
        return (
            f"{self.voter.voter_name} assigned to station "
            "{self.station_id} at {self.center.center_name}"
        )
