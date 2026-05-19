import sqlite3
def main():
    conn = sqlite3.connect('/app/data/soc_data.db')
    for row in conn.execute('select distinct dispositivo, ip_origen from logs'):
        print(row)
if __name__ == '__main__':
    main()
