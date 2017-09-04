from CeleryTask.managers import base
from DB.api import resource, motion, activity


class ActivityCounter(base.BaseTask):
    """
    The task class is to calculate the sum total of the activities
    """
    def __init__(self, time_period):
        self.start = time_period[0]
        self.end = time_period[1]

    @staticmethod
    def _list_active_motion_sensors():
        return resource.list_resource(status=True, sensor_type_id=2)

    def run(self):
        motions = self._list_active_motion_sensors()
        for m in motions:
            count = motion.get_data_by_time(self.start, self.end, m.get('id'))
            count = 0 if not count else count[0][0]

            record = activity.get_activity(False, resource_id=m.get('id'))
            if not record:
                activity.new({
                    'resource_id': m.get('id'),
                    'total': count
                })
            else:
                activity.update_activity(resource_id=m.get('id'), total=count)


