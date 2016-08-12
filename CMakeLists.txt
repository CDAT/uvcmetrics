cmake_minimum_required(VERSION 2.8)
CMAKE_POLICY(SET CMP0012 NEW)

# Project name and initial checks
#=============================================================================
project(metrics)

set(UVCMETRICS_TEST_DATA_DIRECTORY ${metrics_SOURCE_DIR}/test/data CACHE PATH "DIR FOR UVCMETRICS TEST DATA" )
set(LLNL_URL http://uv-cdat.llnl.gov/cdat/resources)

file(READ "${metrics_SOURCE_DIR}/test/data/md5s.txt" UVCMETRICS_FILES)
string(REGEX REPLACE ";" "\\\\;" UVCMETRICS_FILES "${UVCMETRICS_FILES}")
string(REGEX REPLACE "\n" ";" UVCMETRICS_FILES "${UVCMETRICS_FILES}")

message("[INFO] Checking Data Files Are Present And Valid")
foreach(line ${UVCMETRICS_FILES})
    string(REGEX REPLACE " +" ";" line "${line}")
    list(GET line 1 base_file_path)
    list(GET line 0 FILE_MD5)

    string(STRIP "${base_file_path}" base_file_path)
    string(STRIP "${FILE_MD5}" FILE_MD5)
    set(FILE_PATH "${UVCMETRICS_TEST_DATA_DIRECTORY}/${base_file_path}")
    list(APPEND UVCMETRICS_DOWNLOAD_FILES "${FILE_PATH}")

    set(FILE_URL "${LLNL_URL}/../sample_data/uvcmetrics_2.4.1/${base_file_path}")
    set(DOWNLOAD_FILE ON)

    # used variables:
    #   FILE_URL    The url where the file is available
    #   FILE_PATH   The destination for the file
    #   FILE_MD5    The expected md5

    # check if the file already exists
    if(EXISTS "${FILE_PATH}")
      message("CHECKING : ${base_file_path} md5: ${FILE_MD5}")
      # check md5sum
      file(MD5 "${FILE_PATH}" output_md5)

      if(${output_md5} STREQUAL ${FILE_MD5})
          set(DOWNLOAD_FILE OFF)
      else()
          message("\t[INFO] Invalid md5, redownloading")
      endif()
    endif()

    if (DOWNLOAD_FILE)
        message("FECTHING: ${base_file_path} md5: ${FILE_MD5}")
        # add a build target to download the file
        file(DOWNLOAD "${FILE_URL}" "${FILE_PATH}" STATUS stat)
        list(GET stat 0 exit_code)
        list(GET stat 1 msg)

        # fail on error
        if(NOT exit_code EQUAL 0)
          file(REMOVE "${FILE_PATH}")
          message(FATAL_ERROR "Error downloading: ${msg}")
        endif()
    endif()
endforeach()

include(CTest)

add_subdirectory(test)
