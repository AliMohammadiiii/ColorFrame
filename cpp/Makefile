ifeq ($(origin CXX),default)
CXX := c++
endif
CXXFLAGS ?= -std=c++17 -O3 -DNDEBUG -Wall -Wextra -Wpedantic -Werror
BUILD    := build

all: $(BUILD)/colorframe

$(BUILD):
	mkdir -p $(BUILD)

$(BUILD)/colorframe: src/main.cpp src/colorframe.cpp src/colorframe.hpp | $(BUILD)
	$(CXX) $(CXXFLAGS) -o $@ src/main.cpp src/colorframe.cpp

$(BUILD)/unit_tests: tests/unit_tests.cpp src/colorframe.cpp src/colorframe.hpp | $(BUILD)
	$(CXX) $(CXXFLAGS) -Isrc -o $@ tests/unit_tests.cpp src/colorframe.cpp

test: $(BUILD)/unit_tests
	$(BUILD)/unit_tests

clean:
	rm -rf $(BUILD)

.PHONY: all test clean
