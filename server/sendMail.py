import smtplib
def send_mail(receiver,mailText):
	gmail_user = 'cs308.riskgame@gmail.com'  
	gmail_password = 'riskriskrisk'

	server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
	server.ehlo()
	server.login(gmail_user, gmail_password)
	server.sendmail(gmail_user,receiver,mailText)
	server.close()

