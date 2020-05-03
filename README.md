# Video Processing Demo - Frame Extraction
Video processing in Pachyderm! 

This repository has a Python (multi-process) script to extract the frames of a video (for use in machine learning applications). We then deploy the script using a Pachyderm pipeline to parallelize it over a lot of video files.

[Pachyderm](www.pachyderm.com) is an easy to use pipelining and versioning system for data processing. It makes it easy to deploy and update processing pipelines. This can be really useful for iterating on and scaling a data-centered pipeline like video processing. 

We will be taking input videos: 
```
samples/
├── my_tictoc_dance.mp4
├── cat_laser.ogv
└── guitar_shred.ogv
```

And output:
```
output/
└── my_tictoc_dance.mp4
│   ├── 0000000000.jpg
│   ├── 0000000001.jpg
│   ...
│   └── 0000002020.jpg
└── cat_laser.ogv
│   ├── 0000000000.jpg
│   ├── 0000000001.jpg
...
```

## Installation
The script can be installed from source and run with Python3 and OpenCV, with Docker, or with Pachyderm. 

### Docker
You can pull the Docker image by running: 
```
docker pull jimmywhitaker/videoproc:latest
```

### Pachyderm

This example uses a Pachyderm deployment. You can deploy a cluster on [PacHub](hub.pachyderm.com) or deploy locally as described here:

- [Pachyderm Getting Started](https://docs.pachyderm.com/latest/getting_started/)

### From Source
To install locally, you will need Python3 and OpenCV. Clone this repo and install the requirements: 
```
git clone https://github.com/JimnyCricket/videoproc.git
cd videoproc
pip install -r requirements.txt
```

## Frame Extraction 
The frame extraction script is pretty straight-forward. The available options are: 
```
usage: extract_frames.py [-h] [--input DIR] [--output-dir DIR] [--fps FPS]
                         [--threaded]

Video frame extractor

optional arguments:
  -h, --help        show this help message and exit
  --input DIR       input video or directory of videos
  --output-dir DIR  output directory for extracted frames
  --fps FPS         Frames per second (-1 for all frames)
  --threaded        Run the extraction with multiple threads
```


It can be run from the command line like follows: 
```
python extract_frames.py --input ./samples/elephant_small.ogv --output-dir ./output
```

Or, with Docker: 

```
docker run -it -v $(pwd)/:/data jimmywhitaker/videoproc:latest python extract_frames.py --input /data/samples/elephant_small.ogv --output-dir /data/output --threaded
```



## Deploy Script with Pachyderm
Once you have a Pachyderm cluster up and running, you can deploy the frame extractor script to process many videos simultaneously. 

### TLDR;

```bash
# Create data repository
pachctl create repo videos

# Create pipeline
pachctl create pipeline -f frames.json # automatically creates an output repo "frames"

# Add a file to kick off the pipeline
pachctl put file videos@master:small.ogv -f samples/small.ogv  

pachctl list file videos@master  

# Monitor the job
pachctl list job
pachctl logs --pipeline=frames

# Show the output files
pachctl list file frames@master:/small.ogv  

# Download one of the frames
pachctl get file frames@master:/small.ogv/0000000084.jpg -o ./example_frame.jpg  

```