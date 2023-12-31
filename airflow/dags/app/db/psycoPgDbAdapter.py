import os
import psycopg2
import psycopg2.extras as extras
from datetime import date

from helpers.utils import dfToTuples
# Clase de la base de datos mediante psycopg2. Se encarga de generar la conexión a la BD y 
# se irán agregando funciones a medida que vaya creciendo el proyecto
class dbClass:
    def __init__(self):
        self.database = os.getenv("DB_NAME")
        self.username = os.getenv("DB_USERNAME")
        self.schema = os.getenv("DB_SCHEMA") 
        self.password = os.getenv("DB_PASSWORD")
        self.host = os.getenv("DB_CONNECTION")
        self.port = os.getenv("DB_PORT")
        self.conn = self.createDBConnection()
        self.cur = self.conn.cursor()

    def createDBConnection(self):
        try:
            conn = psycopg2.connect(
                dbname=self.database,
                user=self.username,
                password=self.password,
                host=self.host,
                port=self.port
            )
            return conn
        except Exception as e:
            print(f"Error creating database connection: {e}")

    def verifyTableExist(self, tableName):
        try:
            self.cur.execute(f"SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = %s AND table_name = %s);", (self.schema, tableName))
            return self.cur.fetchone()[0]
        except Exception as e:
            print(f"Error verifying table existence: {e}")

    def getCursor(self):
        return self.cur

    def endConnection(self):
        try:
            self.cur.close()
            self.conn.close()
        except Exception as e:
            print(f"Error closing connection: {e}")

    def createTable(self, tableName, createTableQuery):
        try:
            if not self.verifyTableExist(tableName):
                self.cur.execute(createTableQuery)
                self.conn.commit()
                print(f'La tabla de nombre {tableName} ha sido creada de forma exitosa\n')
            else:
                print(f'La tabla de nombre {tableName} ya existe\n')
        except Exception as e:
            print(f"Error creating table: {e}")
            exit(1)

    def executeReadQuery(self, query):
        cursor = self.cur
        result = None
        try:
            cursor.execute(query)
            result = cursor.fetchall()
            return result
        except Exception as e:
            print(f"Error '{e}' ha ocurrido")

    def insertToBd(self, tableName, dataFrame):
        tuples = dfToTuples(dataFrame)
        # Comma-separated dataframe columns
        cols = ','.join(list(dataFrame.columns))
        # SQL quert to execute
        query  = "INSERT INTO %s(%s) VALUES %%s" % (tableName, cols)
        cursor = self.cur
        try:
            extras.execute_values(cursor, query, tuples)
            self.conn.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            print("Error: %s" % error)
            self.conn.rollback()
            cursor.close()
            return 1
        cursor.close()

    def createPropertiesTable(self, tableName):
        createTableQuery = f"""
            CREATE TABLE IF NOT EXISTS {self.schema}.{tableName} (
                property_id VARCHAR,
                last_sold_date DATE,
                status VARCHAR,
                country VARCHAR,
                state VARCHAR,
                type VARCHAR,
                beds INT,
                lot_sqft INT,
                sqft INT,
                city VARCHAR,
                list_price INT,
                created_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (property_id, last_sold_date)
            );
            """
        self.createTable(tableName, createTableQuery)

    def createDateValidationTable(self, tableName):
        createTableQuery = f"""
        CREATE TABLE IF NOT EXISTS {self.schema}.{tableName} (
            date_id INT IDENTITY(0,1),
            read_date DATE,
            created_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (date_id)
        );
        """
        self.createTable(tableName, createTableQuery)

    def dateValidation(self, tableName, validationDate):
        selectQuery = f"""
                SELECT
                    CASE 
                    WHEN count(read_date) >= 1 THEN 1
                    WHEN count(read_date) = 0 THEN 0
                END existense
                FROM {self.schema}.{tableName} WHERE '{validationDate}' = read_date 

        """

        queryResult = self.executeReadQuery(selectQuery)

        if queryResult[0][0] == 1:
            return True
        else: 
            return False
