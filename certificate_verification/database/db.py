import mysql.connector


def get_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="your_password",
        database="rpc_verification"
    )

    return connection

def find_certificate(certificate_data):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT * FROM certificates
        WHERE name = %s
        AND course = %s
    """

    cursor.execute(
        query,
        (
            certificate_data.get("name"),
            certificate_data.get("course")
        )
    )

    result = cursor.fetchone()

    cursor.close()
    connection.close()

    return result

if __name__ == "__main__":
    certificate_data = {
        "name": "Shreelakshmi K S",
        "course": "Software Engineering"
    }

    result = find_certificate(certificate_data)

    print(result)