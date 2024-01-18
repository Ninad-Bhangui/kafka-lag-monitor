from collections import namedtuple
KafkaEntry = namedtuple("KafkaEntry", "group topic partition lag")
RemoteDetails = namedtuple("RemoteDetails", "username hostname key_filename")