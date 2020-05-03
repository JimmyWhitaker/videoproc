from concurrent.futures import ProcessPoolExecutor, as_completed
import argparse
import cv2
import multiprocessing
import os
import sys
from math import ceil as ceil

parser = argparse.ArgumentParser(description="Video frame extractor")
parser.add_argument("--input",
                    metavar="DIR",
                    help="input video or directory of videos",
                    default="./samples")
parser.add_argument("--output-dir",
                    metavar="DIR",
                    default="./output",
                    help="output directory for extracted frames")
parser.add_argument("--fps",
                    default=-1,
                    type=int,
                    help="Frames per second (-1 for all frames)")
parser.add_argument("--threaded",
                    action="store_true",
                    help="Run the extraction with multiple threads (1 thread/CPU)")


def extract_frames(video_path,
                   frames_dir,
                   overwrite=False,
                   start=-1,
                   end=-1,
                   sample_rate=1):
    """Extract the frames from a video clip using OpenCV.

    Args:
        video_path (str): path of the video
        frames_dir (str): directory to save the frames
        overwrite (bool): overwrite frames that already exist?
        start (int): start frame (-1 for start of video)
        end (int): end frame (-1 for end of video)
        sample_rate (int): save every N frames

    Returns:
        Count of images saved (int)
    """

    # Get the video filename from the path
    _, video_filename = os.path.split(video_path)

    # Open the video using a Caputre object
    capture = cv2.VideoCapture(video_path)

    # Start at the beginning if not given a start
    if start < 0:
        start = 0
    # End is end of the video if not specified
    if end < 0:
        end = int(capture.get(
            cv2.CAP_PROP_FRAME_COUNT)) - 1  # last frame of video

    capture.set(1, start)  # set the starting frame
    frame = start  # track current frame
    saved_count = 0  # track how many frames are saved

    while frame < end:  # loop through frames
        success, image = capture.read()  # read the image from the capture

        # Save the frame, according to the desired sample rate
        if (success and frame % sample_rate == 0):
            save_path = os.path.join(frames_dir, video_filename,
                                     "{:010d}.jpg".format(frame))
            # Save if it doesn't exist or if we want to overwrite
            if (not os.path.exists(save_path) or overwrite):
                cv2.imwrite(save_path, image)
                saved_count += 1
        frame += 1

    capture.release()  # Close the capture

    return saved_count


def process_video(video_path,
                  frames_dir,
                  threaded=False,
                  fps=-1,
                  overwrite=False,
                  chunk_size=500):
    """Prepare output directory, compute sample rate, and split video for
    multi-processing (if enabled).

    Args:
        video_path (str): path to the video
        frames_dir (str): directory to save the frames
        overwrite (bool): overwrite frames if they exist?
        fps (int): frames per second to extract
        chunk_size (int): how many frames to split into chunks (one chunk per cpu core process)

    Returns:
        Path to the directory where the frames were saved, or None if fails
    """

    # Get the video filename from the path
    _, video_filename = os.path.split(video_path)

    # Make directory to save frames (filename as directory name)
    os.makedirs(os.path.join(frames_dir, video_filename), exist_ok=True)

    # Open the video using a Caputre object
    capture = cv2.VideoCapture(video_path)
    total_frames = int(capture.get(
        cv2.CAP_PROP_FRAME_COUNT))  # get its total frame count

    # Compute sample rate from FPS
    sample_rate = 1
    if fps != -1:
        sample_rate = ceil(capture.get(cv2.CAP_PROP_FPS) / fps)
    capture.release()  # cose the capture

    # Extract frames
    print("Extracting frames from {}".format(video_filename))
    if not threaded:  # single Process
        extract_frames(video_path,
                       frames_dir,
                       overwrite=overwrite,
                       sample_rate=sample_rate)
    else:  # multiple processes
        # Split the frames into chunk lists
        frame_chunks = [[i, i + chunk_size]
                        for i in range(0, total_frames, chunk_size)]

        # Ensure last chunk has correct end frame
        frame_chunks[-1][-1] = min(frame_chunks[-1][-1], total_frames - 1)

        # Multi-process according to number of cores (gets CPU count automatically)
        with ProcessPoolExecutor(
                max_workers=multiprocessing.cpu_count()) as executor:

            futures = [
                executor.submit(
                    extract_frames,
                    video_path,
                    frames_dir,
                    overwrite=overwrite,
                    start=f[0],
                    end=f[1],
                    sample_rate=sample_rate,
                ) for f in frame_chunks
            ]  # submit the processes: extract_frames(...)

        return os.path.join(
            frames_dir,
            video_filename)  # return directory containing the frames


def main():
    args = parser.parse_args()

    # Create a list of input files
    video_paths = []
    if os.path.isfile(args.input):  # path is a file
        video_paths.append(args.input)
    elif os.path.isdir(args.input):  # path is a directory
        for f in os.listdir(args.input):
            video_paths.append(os.path.join(args.input, f))

    # Extract frames from videos in the input directory
    for input_path in video_paths:
        _ = process_video(
            video_path=input_path,
            frames_dir=args.output_dir,
            threaded=args.threaded,
            fps=args.fps,
            overwrite=False,
            chunk_size=1000,
        )


if __name__ == "__main__":
    main()
