import logging
import azure.functions as func
import psycopg2
import os
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def main(msg: func.ServiceBusMessage):

    notification_id = int(msg.get_body().decode('utf-8'))
    logging.info('Python ServiceBus queue trigger processed message: %s',notification_id)

# Connection to database

    conn = psycopg2.connect(user="Aditya@adi-techconf",
                                  password="P@ssword",
                                  host="adi-techconf.postgres.database.azure.com",
                                  port="5432",
                                  database="techconfdb")
    cur = conn.cursor()

    try:
        cur.execute("SELECT subject, message FROM notification WHERE id={};".format(notification_id))
        rows=cur.fetchall()
        rows=rows[0]
        subject = str(rows[0])
        body = str(rows[1])
        # Get attendees email and name
        cur.execute("SELECT email, first_name FROM attendee;")
        attendees = cur.fetchall()
        # Loop through each attendee and send an email with a personalized subject
        for (email, first_name) in attendees:
            mail = Mail(
                from_email='info@techconf.com',
                to_emails= email,
                subject= subject,
                plain_text_content= "Hi {}, \n {}".format(first_name, body))
            try:
                SENDGRID_API_KEY = os.environ['SENDGRID_API_KEY']
                sg = SendGridAPIClient(SENDGRID_API_KEY)
                response = sg.send(mail)
            except Exception as e:
                logging.error(e)
        status = "Notified {} attendees".format(len(attendees))

        # Update the notification table by setting the completed date and updating the status with the total number of attendees notified
        cur.execute("UPDATE notification SET status = '{}', completed_date = '{}' WHERE id = {};".format(status, datetime.utcnow() , notification_id))        
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        logging.error(error)
        conn.rollback()
    finally:
        cur.close()
        conn.close()
