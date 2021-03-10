def limitJson(buffer, limit=60):
    for json in buffer:
        owner, data = json['owner'], json['data']
        dataLimited = [x for x in data if x[0] <= limit]
        yield { 'owner': owner, 'data': dataLimited }