import csv

with open('pipeID.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    for row in csv_reader:
        if line_count == 0:
            print(f'Column names are {", ".join(row)}')
            line_count += 1
        else:
            print(f'\t ID= {row[0]} {row[1]} NPS sch = {row[2]} Inside Dia = {row[3]}.')
            line_count += 1
    print(f'Processed {line_count} lines.')
