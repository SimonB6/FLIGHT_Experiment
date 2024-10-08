
#pragma once

#include <vector>
#include <string>
#include <assert.h>
#include <limits.h>
#include <array>
#include <json.hpp>

// AES globals
#define RANDOM_COMPUTE 256	//Size of buffer for random elements
#define STRING_BUFFER_SIZE 256

// GPU configuration
#define MAX_THREADS_PER_BLOCK 32

// MPC globals
#ifndef FLOAT_PRECISION
#define FLOAT_PRECISION 12
#endif
#define GFORCE_BOUND (uint64_t) 1 << 24
#define ROGUE_BOUND (uint64_t) 1 << 24
#define PC_BITS 24
#define ENABLE_OFFLINE_RANDOMNESS false

// NN globals
#ifndef DELTA_DATATYPE
#define DELTA_DATATYPE uint32_t
#endif

// the other settings
#define PRELOAD_PATH "files/preload/"
#define TEST_PATH "files/test/"

#define MAX_JSON_DESERIALIZATION_BUFFER 1048576

extern int MINI_BATCH_SIZE;
extern int LOG_MINI_BATCH;

// learning rate = 2^(-LOG_LEARNING_RATE)
extern int log_learning_rate;

