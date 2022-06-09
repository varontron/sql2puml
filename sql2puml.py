import pyodbc
import sys
import getopt

from tabledef import Tabledef
from columndef import Columndef
from relationdef import Relationdef

def Connect(driverOverride, server, host, port, dbname, username, password):

    if server == 'mssql':
        driver = '{SQL Server}'
        if driverOverride != '':
            driver = driverOverride
        
        if (port != '1433'):
            thePort = ',' + port
        else:
            thePort = ''

        if username == '':
            #Driver={SQL Server};Server=myServerAddress;Database=myDataBase;Trusted_Connection=Yes;
            connstr = ('Driver=' + driver + ';'
                    'Server=' + host + thePort + ';'
                    'Database=' + dbname +
                    ';Trusted_Connection=yes;')
        else:
            # Driver={SQL Server};Server=myServerAddress;Database=myDataBase;Uid=myUsername;Pwd=myPassword;
            connstr = ('Driver=' + driver + ';'
                    'Server=' + host + thePort + ';'
                    'Database=' + dbname +
                    ';Uid=' + username + ';Pwd=' + password + ';'
                    )
    elif server == 'mysql':
        # Driver={MySQL ODBC 8.0 Unicode Driver};Server=myServerAddress;Port=3306;Database=myDataBase;User=myUsername;Password=myPassword;Option=3;
        driver = '{MySQL ODBC 8.0 Unicode Driver}'
        if driverOverride != '':
            driver = driverOverride
        connstr = ('Driver=' + driver + ';'
                'Server=' + host + ';Port=' + port + ';' + 'Database=' + dbname +
                ';User=' + username + ';Password=' + password + ';Option=3;'
                )
    
    connection = pyodbc.connect(connstr)
    return connection


def Disconnect(connection) -> None:
    connection.close()


def EmitPumlHeader(dbname, zerorows):
    print('@startuml ' + dbname + '\n')
    print('skinparam Linetype ortho\n')
    if zerorows:
        if zerorows == 'show':
            print("""hide stereotype
hide circle            
skinparam class<<empty>> {
  backgroundColor #FFF
  borderColor #CCC
  fontColor #CCC
}""")
        else:
            print(f"{zerorows} <<empty>>\n")


def EmitPumlFooter():
    print('\n@enduml')


# Use table name lowercased and with spaces replaced by underscores
def PumlName(sqlName) -> str:
    pumlName = sqlName.lower().replace(' ', '_')
    return pumlName

def EmitTableHeader(tablename, rowcount):    
    stereotype = " <<empty>> " if rowcount is not None and rowcount == 0 else ""
    print('entity "' + tablename + '" as ' + PumlName(tablename) + stereotype + ' {')


def EmitTableDef(connection, table:Tabledef, zerocols:str):
    line = ''
    seperated = False

    for columnName, column in table.Columns.items():
        line = ""
        if zerocols is not None and zerocols == "show" and column.Rows == 0:
            line += "<color:#CCC>"

        if zerocols is None or column.Rows > 0:
            line += "\t"

        if zerocols is None or zerocols == "show":
            if column.IsKey == False:               # Put out primary key seperator
                if seperated == False:              # before the first non primary key column
                    print("\t--")
                    seperated = True

            if column.IsMandatory:
                line += '* '
            
            line = line + column.Name
            if column.IsUnique:
                line += '*'

            line = line + ':' + column.Datatype            

        if zerocols is not None and zerocols == "show" and column.Rows == 0:
            print(f"{line}</color>")
        else:
            print(line)


def EmitTableFooter():
    print('}\n')


def EmitTable(connection, table:Tabledef, zerorows:str, zerocols:str):
    EmitTableHeader(table.Name, table.RowCount)
    EmitTableDef(connection, table, zerocols)
    EmitTableFooter()

def EmitRelations(connection, table:Tabledef):
    for name, rel in table.Relationships.items():
        print(PumlName(rel.PrimaryTable.Name) + ' ' + rel.PumlRelation + ' ' + PumlName(rel.ForeignTable.Name))


def printStderr(*a): 
	# Here a is the array holding the objects 
	# passed as the arguement of the function 
	print(*a, file = sys.stderr) 


def PrintUsage():
    printStderr('Usage: python sql2puml.py OPTIONS [FILE]')
    printStderr('OPTIONS')    
    printStderr('\t-d, --database <database name>\tName of database to get diagram for')    
    printStderr('\t[-s, --schema <schema name>]\tName of schema within the database, default dbo with SQL Server')
    printStderr('\t[-S, --server <RDBMS Server>]\tSupply one of mssql, mysql. Default is mssql')
    printStderr('\t[-h, --host <server name>]\tServer to connect to, default localhost')
    printStderr('\t[-p, --port <SQL listen port>]\tPort to connect to, default 1433')
    printStderr('\t[-o, --out <output filename>]\tFilename to save output to, default write to console')
    printStderr('\t[-u, --user <username>]\tUsername to connect as')
    printStderr('\t[-P, --password <password>]\tPassword to connect with')
    printStderr('\t[-z, --zerorows <mode>]\tSupply one of show, hide, remove. Default is None, i.e., empty tables appear normally')
    printStderr('\t[-Z, --zerocols <mode>]\tSupply one of show, remove. Default is None, i.e., columns appear normally')
    printStderr('\nExample: python sql2puml.py -server localhost -port 1433 -dbname pubs -schema dbo')


def main(argv) -> None:
    server = 'mssql'
    host = 'localhost'
    port = '1433'
    dbname = ''
    schema = ''
    filename = ''
    conn = None
    fileHandle = None
    username = ''
    password=''
    driver = ''
    zerorows = None

    try:
        opts, args = getopt.getopt(argv, 'S:d:s:h:p:o:u:P:D:z:Z:', ['server=','database=','schema=','host=','port=','out=','user=','password=','driver=','zerorows=','zerocols='])
        for opt, arg in opts:
            if opt in ('-S', '--server'):
                server = arg.lower()
            elif opt in ('-d', '--database'):
                dbname = arg 
            elif opt in ('-s', '--schema'):
                schema = arg
            elif opt in ('-h', '--host'):
                host = arg
            elif opt in ('-p', '--port'):
                port = arg
            elif opt in ('-o', '--out'):
                filename = arg
            elif opt in ('-u', '--user'):
                username = arg
            elif opt in ('-P', '--password'):
                password = arg
            elif opt in ('-D', '--driver'):
                driver = arg
            elif opt in ('-z', '--zerorows'):
                zerorows = arg
            elif opt in ('-Z', '--zerocols'):
                zerocols = arg

        if filename != '':            
            original_stdout = sys.stdout
            fileHandle = open(filename, 'w')                # Change the standard output to filename
            sys.stdout = fileHandle

        if dbname == '':
            raise ValueError('No database name supplied')

        if server == 'msql':
            schema = ''

        if server == 'mssql' and schema == '':
            schema = 'dbo'

        conn = Connect(driver, server, host, port, dbname, username, password)
        tables = Tabledef.Get(conn, schema, zerorows, zerocols)
        EmitPumlHeader(dbname, zerorows)
        for name, table in tables.items():
            EmitTable(conn, table, zerorows, zerocols)

        for name, table in tables.items():
            EmitRelations(conn, table)

        EmitPumlFooter()

    except getopt.GetoptError:
        PrintUsage()

    except ValueError as ve:
        PrintUsage()

    except Exception as e:
        printStderr('EXCEPTION: ' + e.args[1])
    
    finally:
        if fileHandle != None:
            sys.stdout = fileHandle

        if conn != None:
            Disconnect(conn)

if __name__ == '__main__':
    main(sys.argv[1:])
