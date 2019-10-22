import socket

from botocore.waiter import WaiterModel, create_waiter_with_client


class TrafficMirrorService(object):
    # region traffic mirror sessions
    @staticmethod
    def create_traffic_mirror_session(ec2_client, fulfillment, tags):
        response = ec2_client.create_traffic_mirror_session(
            NetworkInterfaceId=fulfillment.source_nic_id,
            TrafficMirrorTargetId=fulfillment.traffic_mirror_target_id,
            TrafficMirrorFilterId=fulfillment.traffic_mirror_filter_id,
            SessionNumber=int(fulfillment.session_number),
            Description=fulfillment.session_name,
            TagSpecifications=[
                {
                    'ResourceType': 'traffic-mirror-session',
                    'Tags': tags
                }
            ]
        )
        return response['TrafficMirrorSession']['TrafficMirrorSessionId']

    @staticmethod
    def find_sessions_by_session_names(ec2_client, session_names):
        """
        :param list(str) session_names:
        """
        traffic_mirror_sessions = []
        response = ec2_client.describe_traffic_mirror_sessions(
            Filters=[
                {
                    'Name': 'description',
                    'Values': session_names
                },
            ],
            MaxResults=100)
        traffic_mirror_sessions.extend(response['TrafficMirrorSessions'])
        while 'NextToken' in response:
            response = ec2_client.describe_traffic_mirror_sessions(NextToken=response['NextToken'])
            traffic_mirror_sessions.extend(response['TrafficMirrorSessions'])
        return {t['Description']: t for t in traffic_mirror_sessions}


    @staticmethod
    def find_mirror_session_ids_by_reservation_id(ec2_client, reservation_id):
        """
        :param uuid.uuid4 reservation_id:
        """
        traffic_mirror_sessions = []
        response = ec2_client.describe_traffic_mirror_sessions(
            Filters=[
                {
                    'Name': 'tag:ReservationId',
                    'Values': [
                        str(reservation_id)
                    ]
                },
            ],
            MaxResults=100)
        traffic_mirror_sessions.extend(response['TrafficMirrorSessions'])
        while 'NextToken' in response:
            response = ec2_client.describe_traffic_mirror_sessions(NextToken=response['NextToken'])
            traffic_mirror_sessions.extend(response['TrafficMirrorSessions'])
        return [t['TrafficMirrorSessionId'] for t in traffic_mirror_sessions]

    # endregion

    # region traffic mirror filters
    @staticmethod
    def create_filter(ec2_client, tags):
        description = str(tags[0]['Value'])
        response = ec2_client.create_traffic_mirror_filter(
            Description=description,
            TagSpecifications=[
                {
                    'ResourceType': 'traffic-mirror-filter',
                    'Tags': tags
                },
            ])

        return response['TrafficMirrorFilter']['TrafficMirrorFilterId']

    @staticmethod
    def find_traffic_mirror_filter_ids_by_reservation_id(ec2_client, reservation_id):
        traffic_mirror_filters = []
        response = ec2_client.describe_traffic_mirror_filters(
            Filters=[
                {
                    'Name': 'tag:ReservationId',
                    'Values': [
                        str(reservation_id)
                    ]
                },
            ],
            MaxResults=123)

        traffic_mirror_filters.extend(response['TrafficMirrorFilters'])
        while 'NextToken' in response:
            response = ec2_client.describe_traffic_mirror_filters(NextToken=response['NextToken'])
            traffic_mirror_filters.extend(response['TrafficMirrorFilters'])

        return [traffic_filter['TrafficMirrorFilterId'] for traffic_filter in traffic_mirror_filters]

    # region traffic mirror rules
    def create_filter_rules(self, ec2_client, fulfillment):
        """
        creates filter rules requested for a particular session
        :param cloudshell.cp.aws.models.traffic_mirror_fulfillment.TrafficMirrorFulfillment fulfillment:
        """
        i = 0
        for rule in fulfillment.filter_rules:
            i += 1
            description = 'filter_rule_{0}_{1}'.format(i, fulfillment.traffic_mirror_filter_id)
            kwargs = {
                'TrafficMirrorFilterId': fulfillment.traffic_mirror_filter_id,
                'RuleAction': 'accept',
                'Description': description
            }

            if rule.sourcePortRange:
                kwargs['SourcePortRange'] = rule.sourcePortRange

            if rule.destinationPortRange:
                kwargs['DestinationPortRange'] = rule.destinationPortRange

            kwargs['TrafficDirection'] = rule.direction
            kwargs['RuleNumber'] = i
            kwargs['Protocol'] = rule.protocol if isinstance(rule.protocol, int) else socket.getprotobyname(
                rule.protocol)
            kwargs['DestinationCidrBlock'] = rule.destinationCidr or self._get_destination_cidr()
            kwargs['SourceCidrBlock'] = rule.sourceCidr or self._get_source_cidr()

            ec2_client.create_traffic_mirror_filter_rule(**kwargs)

    @staticmethod
    def _get_source_cidr():
        return '0.0.0.0/0'

    @staticmethod
    def _get_destination_cidr():
        return '0.0.0.0/0'



    # endregion
    # endregion

    # region traffic mirror targets

    @staticmethod
    def create_traffic_mirror_target_from_nic(ec2_client, target_nic, tags):
        description = str(tags[0]['Value'])
        response = ec2_client.create_traffic_mirror_target(NetworkInterfaceId=target_nic,
                                                           Description=description,
                                                           TagSpecifications=[
                                                               {
                                                                   'ResourceType': 'traffic-mirror-target',
                                                                   'Tags': tags
                                                               }
                                                           ])
        return response['TrafficMirrorTarget']['TrafficMirrorTargetId']

    @staticmethod
    def find_traffic_targets_by_nics(ec2_client, target_nics):
        response = ec2_client.describe_traffic_mirror_targets(Filters=[{
            'Name': 'network-interface-id',
            'Values': target_nics}])

        return {x['NetworkInterfaceId']: x['TrafficMirrorTargetId'] for x in response['TrafficMirrorTargets']}

    @staticmethod
    def find_traffic_mirror_targets_by_reservation_id(ec2_client, reservation_id):
        traffic_mirror_targets = []
        response = ec2_client.describe_traffic_mirror_targets(
            Filters=[
                {
                    'Name': 'tag:ReservationId',
                    'Values': [
                        str(reservation_id)
                    ]
                },
            ],
            MaxResults=123)
        traffic_mirror_targets.extend(response['TrafficMirrorTargets'])
        while 'NextToken' in response:
            response = ec2_client.describe_traffic_mirror_filters(NextToken=response['NextToken'])
            traffic_mirror_targets.extend(response['TrafficMirrorTargets'])

        return [target['TrafficMirrorTargetId'] for target in traffic_mirror_targets]

    #endregion

    def _empty(self):
        pass
