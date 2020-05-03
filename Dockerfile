FROM denismakogon/opencv3-slim:edge
MAINTAINER Jimmy Whitaker

WORKDIR /workspace/
ADD . /workspace
RUN pip install --no-cache --no-cache-dir --upgrade -r requirements.txt
RUN rm -fr ~/.cache/pip /tmp*
