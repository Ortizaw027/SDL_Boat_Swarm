# Unmanned Surface Vehicle Swarm

## Project Overview

This project developed a functional swarm of Unmanned Surface Vehicles (USVs) capable of coordinated movement using a centralized controller and a Leader-Follower dynamic approach over a secure LoRa network. The goal was to demonstrate enhanced efficiency, resilience, and safety for maritime tasks compared to single-unit operations.

**Authors:** Dominic Mesagna & Antonio Ortiz

## Key Objectives Achieved

* Developed a functioning swarm of two USVs.
* Integrated GPS and Compass sensors for navigation.
* Established a secure LoRa network for communication.
* Implemented a Centralized Controller for management and monitoring.
* Demonstrated coordinated movement using a Leader-Follower algorithm.

## Technology Highlights

* **Hardware:** Raspberry Pi Zero 2W, NEO-6M GPS, HMC5883L Compass, RYLR896 LoRa, TB6612FNG Motor Driver, custom-integrated RC boat hulls.
* **Software:** Python-based control scripts (`LeaderBoat.py`, `FollowerBoat.py`, `Controller.py`) utilizing `pigpio`, `serial`, and `smbus2` libraries.

## Component Testing Scripts

The `sensor_test_programs` directory within this repository contains dedicated Python scripts designed for the isolated functional verification and characterization of individual hardware components, including motor control, GPS data acquisition, and compass readings. These scripts facilitate granular testing and debugging of the sensor and actuator interfaces prior to integrated system deployment.

## Results Summary

Controlled testing demonstrated coordinated movement and reliable communication between the two USVs. The system successfully integrated sensor data for navigation and maintained communication links for control and telemetry reporting.

## Acknowledgments

This project was made possible with the generous support from Drone City, who aided in the purchasing of the resources used in this project.

## Demo Video

A short video demonstrating the project's results can be found here:

https://youtube.com/shorts/xEofub0lBZo?feature=share
---

