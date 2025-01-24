info = open('./all.csv', 'r')
id_file = open('./all_stock_id.txt', 'w')
for line in info.readlines():
    sp = line.strip().split(',')
    id_file.write(f'{sp[1]},')
    