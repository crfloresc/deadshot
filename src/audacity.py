def createLabels(name, output):
    with open('out/' + name + '.txt', 'w') as file:
        for line in output:
            file.write(str(line[0]) + '\t' + str(line[1]) + '\t' + line[2] + '\n')