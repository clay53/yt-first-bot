from __future__ import print_function

from conf import (playlists, comment, update_freq)
print(playlists)

import os
import sys
import time

import google.oauth2.credentials

import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow

# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret.
CLIENT_SECRETS_FILE = "client_secret.json"

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account and requires requests to use an SSL connection.
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'

def get_authenticated_service():
  flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
  credentials = flow.run_console()
  return build(API_SERVICE_NAME, API_VERSION, credentials = credentials)

def print_response(response):
  print(response)

# Build a resource based on a list of properties given as key-value pairs.
# Leave properties with empty values out of the inserted resource.
def build_resource(properties):
  resource = {}
  for p in properties:
    # Given a key like "snippet.title", split into "snippet" and "title", where
    # "snippet" will be an object and "title" will be a property in that object.
    prop_array = p.split('.')
    ref = resource
    for pa in range(0, len(prop_array)):
      is_array = False
      key = prop_array[pa]

      # For properties that have array values, convert a name like
      # "snippet.tags[]" to snippet.tags, and set a flag to handle
      # the value as an array.
      if key[-2:] == '[]':
        key = key[0:len(key)-2:]
        is_array = True

      if pa == (len(prop_array) - 1):
        # Leave properties without values out of inserted resource.
        if properties[p]:
          if is_array:
            ref[key] = properties[p].split(',')
          else:
            ref[key] = properties[p]
      elif key not in ref:
        # For example, the property is "snippet.title", but the resource does
        # not yet have a "snippet" object. Create the snippet object here.
        # Setting "ref = ref[key]" means that in the next time through the
        # "for pa in range ..." loop, we will be setting a property in the
        # resource's "snippet" object.
        ref[key] = {}
        ref = ref[key]
      else:
        # For example, the property is "snippet.description", and the resource
        # already has a "snippet" object.
        ref = ref[key]
  return resource

# Remove keyword arguments that are not set
def remove_empty_kwargs(**kwargs):
  good_kwargs = {}
  if kwargs is not None:
    for key, value in kwargs.iteritems():
      if value:
        good_kwargs[key] = value
  return good_kwargs

def playlist_items_list_by_playlist_id(client, **kwargs):
    # See full sample for function
    kwargs = remove_empty_kwargs(**kwargs)

    response = client.playlistItems().list(
    **kwargs
    ).execute()

    return response

# Remove keyword arguments that are not set
def remove_empty_kwargs(**kwargs):
  good_kwargs = {}
  if kwargs is not None:
    for key, value in kwargs.iteritems():
      if value:
        good_kwargs[key] = value
  return good_kwargs

def comment_threads_insert(client, properties, **kwargs):
  # See full sample for function
  resource = build_resource(properties)

  # See full sample for function
  kwargs = remove_empty_kwargs(**kwargs)

  response = client.commentThreads().insert(
    body=resource,
    **kwargs
  ).execute()



client = get_authenticated_service()

logDir = ("logs/" + str(time.time()) + ".log")
if not os.path.exists("logs"):
    os.makedirs("logs")
open(logDir, "w+")

def log (log):
    with open(logDir, "a") as l:
        print (log)
        print (log, file=l)

for playlist in playlists:
    video = playlist_items_list_by_playlist_id(client,
        part='contentDetails',
        maxResults=1,
        playlistId=playlist['key']
    )
    video_key = video['items'][0]['contentDetails']['videoId']
    playlist['last'] = video_key

    log ("playlist['last']: " + video_key)
time.sleep(update_freq)
log ("")

while (True):
    for playlist in playlists:
        log ("playlistId: " + playlist['key'])
        video = playlist_items_list_by_playlist_id(client,
            part='contentDetails',
            maxResults=1,
            playlistId=playlist['key']
        )
        video_key = video['items'][0]['contentDetails']['videoId']

        if (playlist['last'] != video_key):
            log (playlist['key'] + "has new video: " + video_key)
            comment_threads_insert(client, {
                    'snippet.videoId': video_key,
                    'snippet.topLevelComment.snippet.textOriginal': comment
                },
                part='snippet'
            )
            playlist['last'] = video_key
        
        log ("videoId: " + video_key)
    time.sleep(update_freq)
    log ("")
