cmake_minimum_required(VERSION 4.3)
project(c_binario C)

set(CMAKE_C_STANDARD 17)

add_executable(c_binario
        src/binary_core.c
        src/main_cli.c
)
target_include_directories(c_binario PRIVATE include)

add_custom_command(TARGET c_binario POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E make_directory "${CMAKE_SOURCE_DIR}/../bin"
        COMMAND ${CMAKE_COMMAND} -E copy "$<TARGET_FILE:c_binario>" "${CMAKE_SOURCE_DIR}/../bin/c_binario.exe"
)