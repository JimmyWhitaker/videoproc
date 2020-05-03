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

## 1. Installation
This demo is meant to deploy the script and show how it can be run with Pachyderm. If we want to test the container or script locally without Pachyderm, we can run it with Docker or install it from source and run with Python3 and OpenCV. There are installation and running instructions for each. 

### Pachyderm

This example uses a Pachyderm deployment for scaling and management. We can deploy a cluster on [PacHub](hub.pachyderm.com) or deploy locally as described here:

- [Pachyderm Getting Started](https://docs.pachyderm.com/latest/getting_started/)

Once everything is up, we can check the setup by running: 
1. `kubectl get all` to ensure all the pods are up. 
2. `pachctl version` which will show both the `pachctl` and `pachd` versions.

### Run Locally: Docker

[Install Docker](https://docs.docker.com/install/) and then pull the image by running:
```
docker pull jimmywhitaker/videoproc:latest
```

### Run Locally: From Source

To install locally, you will need Python3 and OpenCV. Clone this repo and install the requirements:  

```
git clone https://github.com/JimnyCricket/videoproc.git
cd videoproc
pip install -r requirements.txt
```

## 2. Frame Extraction 

The frame extraction script is simple. It reads input videos and writes the frames to an output directory. Additionally, it has: 

1. Optional multi-processing to increase the speed of the frame extraction (1 process per CPU core).
2. Downsample the video to a specific frames per second (FPS). This can be useful if you don't need all the frames for a video and can save a lot on processing. 

The full list of available options are: 

```
usage: extract_frames.py [-h] [--input DIR] [--output-dir DIR] [--fps FPS] [--threaded]

Video frame extractor

optional arguments:
  -h, --help        show this help message and exit
  --input DIR       input video or directory of videos
  --output-dir DIR  output directory for extracted frames
  --fps FPS         Frames per second (-1 for all frames)
  --threaded        Run the extraction with multiple threads
```

The script can be run from the command line:  

```
python extract_frames.py --input ./samples/elephant_small.ogv --output-dir ./output
```

Or, with Docker:  

```  
docker run -it -v $(pwd)/:/data jimmywhitaker/videoproc:latest python extract_frames.py --input /data/samples/elephant_small.ogv --output-dir /data/output --threaded
```



## 3. Deploy Script with Pachyderm

Once we have a Pachyderm cluster up and running, we can deploy the frame extractor script to process many videos simultaneously. We use the `pachctl` command line utility to execute our commands against the cluster.  

### TLDR;  

```bash  
# 1. Create a data repository
pachctl create repo videos

# 2. Create a Pipeline
pachctl create pipeline -f frames.json # automatically creates an output repo "frames"

# 3. Add a video to kick off the pipeline
pachctl put file videos@master:small.ogv -f samples/small.ogv  
pachctl list file videos@master  

# 4. Monitor the job
pachctl list job
pachctl logs --pipeline=frames

# 5. Show the output files
pachctl list file frames@master:/small.ogv  

# 6. Download one of the frames
pachctl get file frames@master:/small.ogv/0000000084.jpg -o ./output/example_frame.jpg  

```  

### Step 1 - Create a Data Repository  

Much like git for code, Pachyderm applies git-like concepts to data. Each new piece of data (referred to as a datum) is versioned and tracked, so we can always know what changes have affected our pipelines. 

In this step, we use `pachctl create repo` to create a new data repository to put our videos. This repo will serve as our input to the pipeline, and we will upload our videos here in step 3.  

We create our data repo by running:  

```
pachctl create repo videos
```

### Step 2 - Create a Pipeline  

Once we have our videos repo, we can deploy the frame extraction pipeline. Pipelines are very powerful concept in Pachyderm. Simply put, they take input files from one repo, process it using code in a Docker image, and output files to a new repo (with the same name as the pipeline). Configuring a pipeline only requires a single json file. In our pipeline, [`frames.json`](frames.json), we define the input repo, the Docker image that contains our code, and the command that will be run to put our frames in the output repo. The output repo is created automatically and will have the same name as our pipeline, i.e. `frames`.

Pachyderm handles the input and output repos in a very intuitive manner. Data is mapped into the container as a file system (Pachyderm File System, or PFS). Our input repo can therefore be accessed at the location `/pfs/videos` and our output files are available at `/pfs/out`.  

Another amazing feature is [glob patterns](https://docs.pachyderm.com/latest/concepts/pipeline-concepts/datum/glob-pattern/). We won't go into it too much here, but this allows us to control how data from the input repo is passed to the container. We could pass all videos to a single container (iterating through the videos one-by-one), or start a container for each video in our input repo, running the computation in parallel and scaling it across our cluster. We do the latter in this demo.  

We create the pipeline by running: 

```
pachctl create pipeline -f frames.json
```

### Step 3 - Add a video to kick off the pipeline

Once the pipeline is created, the docker images is pulled and ready to run. As soon as we add data to the input repo, the Pachyderm will automatically detect the presence of new data and will start a job to process the data. 

We can add one of our sample files by running: 
```
pachctl put file videos@master:small.ogv -f samples/small.ogv  
```

This command probably looks exactly like you would have expected except for the "master" tag in the middle. If you recall all of the data in Pachyderm is versioned, so this is the branch that we're pushing our data to. That means that you can have different data on different branches. Just like coding with git, this gives us the ability to try out data-dependent features on separate branches from our main pipeline.  

We can check to make sure that our video made it to the master branch of the video repo by running: 
```
pachctl list file videos@master 
```

### Step 4 - Monitor the job
Once we added the video the pipeline started running. We can check that a job was started with: 
```
pachctl list job
```

and even inspect the logs for that pipeline with: 
```
pachctl logs --pipeline=frames
```


### Step 5 - Show the output files

Once the pipeline is finished, if it was successful we should be able to see all of the frames that were output for our video with:

```
pachctl list file frames@master:/small.ogv 
```

### Step 6
At this point we've seen some of the power that Pachyderm holds. If we wanted to then download a frame from Pachyderm, we could run:

```
pachctl get file frames@master:/small.ogv/0000000084.jpg -o ./output/example_frame.jpg
```
Or we could add another pipeline that uses the frames repo as input and performs more processing on top of it. 