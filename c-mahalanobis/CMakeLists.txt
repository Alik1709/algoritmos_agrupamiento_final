cmake_minimum_required(VERSION 4.3)
project(c_mahalanobis C)

set(CMAKE_C_STANDARD 17)

add_executable(c_mahalanobis
        src/matrix_math.c
        src/mahalanobis_core.c
        src/main_cli.c
)

target_include_directories(c_mahalanobis PRIVATE include)
target_link_libraries(c_mahalanobis m)

add_custom_command(TARGET c_mahalanobis POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E make_directory "C:/Dev/bin"
        COMMAND ${CMAKE_COMMAND} -E copy "$<TARGET_FILE:c_mahalanobis>" "C:/Dev/bin/c_mahalanobis.exe"
)
