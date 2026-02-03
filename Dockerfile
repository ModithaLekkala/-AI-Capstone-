FROM sde
WORKDIR /binocular
COPY requirements.txt .
RUN $SDE_INSTALL/bin/pip3.10 install -r requirements.txt
