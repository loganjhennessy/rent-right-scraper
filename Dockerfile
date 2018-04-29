FROM ubuntu:17.10

ADD . /opt/rent-right-scraper

# Apt-get stuff
RUN apt-get update
RUN apt-get -y install python3-pip

# Pip stuff
RUN pip3 install --upgrade pip
RUN pip3 install -r /opt/rent-right-scraper/requirements.txt
RUN pip3 install -e /opt/rent-right-scraper

ENTRYPOINT ["python3","/opt/rent-right-scraper/rentrightscraper/main.py"]
