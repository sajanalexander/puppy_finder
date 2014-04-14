import re
import json
import os.path
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from bs4 import BeautifulSoup
from urllib2 import urlopen

URL = "http://www.austinpetsalive.org/adopt/dogs/"
BASE_URL = "http://www.austinpetsalive.org"
FILENAME = 'seen_puppies.json'
EMAIL_CONFIG_FILENAME = 'email.json'

def main():
    email_config = load_email_config()
    seen = load_puppies()
    new_puppies = find_new_puppies(seen)
    email_new_puppies(new_puppies, email_config)
    write_puppies(seen, new_puppies)

def load_email_config():
    with open(EMAIL_CONFIG_FILENAME, 'rb') as f:
        return json.load(f)

def email_new_puppies(puppies, email_config): 
    if (len(puppies) == 0):
        return

    from_email = email_config['from']
    to_email = email_config['to']
    subject = 'New Puppies'
    text = create_text_email_part(puppies)
    html = create_html_email_part(puppies)

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = ",".join(to_email)

    text_part = MIMEText(text, 'plain')
    html_part = MIMEText(html, 'html')

    msg.attach(text_part)
    msg.attach(html_part)

    server = smtplib.SMTP(email_config['smtp'])
    server.ehlo()
    server.starttls()
    server.login(email_config['username'], email_config['password'])
    server.sendmail(from_email, to_email, msg.as_string())
    server.quit()

def create_text_email_line(item):
    info = item[1]
    return info['name'] + ": " + info['url']

def create_text_email_part(puppies):
    return "Here are the new puppies: \n" + "\n".join(map(create_text_email_line, puppies.iteritems()))

def create_html_email_item(item):
    info = item[1]
    return """<li>
        <a href="%s">
            <h3>%s</h3>
            <img src="%s"></img>
        </a>
    </li>""" % (info['url'], info['name'], info['img'])

def create_html_email_part(puppies):
    return """
        <html>
            <body>
                <ul>
                   %s 
                </ul>
            </body>
        </html>
    """ % "\n".join(map(create_html_email_item, puppies.iteritems()))

def load_puppies(): 
    if not os.path.isfile(FILENAME):
        return {}
    with open(FILENAME, 'rb') as f:
        return json.load(f)


def write_puppies(seen, new_puppies): 
    for puppy_id in new_puppies:
        seen[puppy_id] = new_puppies[puppy_id]

    with open(FILENAME, 'wb') as f:
        json.dump(seen, f)

def find_new_puppies(seen): 
    html = urlopen(URL).read()
    soup = BeautifulSoup(html, "lxml")
    sections = soup.findAll("li", "pet")

    new_puppies = {}

    for section in sections: 
        anchor = section.find("a")
        link = anchor["href"]
        id_match = re.search("ID=(.*)", link)
        if id_match == None:
            continue
        puppy_id = id_match.group(1)

        if not (puppy_id in seen):
            name = str(section.find("h3").string)
            img = section.find("img")
            img_src = img["src"]
            puppy_url = BASE_URL + link
            new_puppies[puppy_id] = { 'name': name, 'img': img_src, 'url': puppy_url }

    return new_puppies


if __name__ == "__main__":
    main()
