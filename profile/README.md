# **SmartPot: Automated Hydroponic Garden Management System**

**SmartPot** is a software system designed for managing and automating hydroponic gardens, with a focus on tomato and lettuce crops. By integrating Internet of Things (IoT) technologies, SmartPot provides a comprehensive solution for optimizing plant care, minimizing manual intervention, and ensuring sustainable agricultural practices.

## **Project Overview:**

- **Advanced Simulation:** Using the Wokwi platform to simulate sensors and actuators, allowing for precise development and testing without the need for physical hardware.
- **Complete Software Solution:** Development of a system that includes a database, efficient backend, intuitive frontend, data analytics capabilities, and process automation systems.
- **Real-time Monitoring:** Virtual sensors measure critical parameters such as humidity, light, temperature, pH, and nutrient levels.
- **Automated Control:** Algorithms adjust cultivation conditions based on sensor data and crop-specific standards, ensuring optimal plant growth.
- **Customizable Prototype:** Focused on hydroponic gardens for tomatoes and lettuce, with the flexibility to add or remove sensors and actuators as needed.

## **Key Features:**

- **Real-time Control:** Monitor and control environmental conditions, irrigation, and lighting.
- **API Integration:** Real-time access to data and control via a custom API.
- **User Interface:** An intuitive web portal to manage and visualize the garden's status, sensor data, and automated processes.
- **Automation:** Control of irrigation, lighting, and other environmental factors based on sensor readings.
- **Data Analysis:** Historical data tracking with reports and analytics to optimize plant growth.
  
### Technologies Used:
- **IoT Integration**: Simulation of hardware using **Wokwi** with virtual sensors (temperature, humidity, pH, light, and nutrient levels). The ESP32 microcontroller is programmed with **MicroPython** to interact with the virtual sensors and send real-time data to the backend.
- **Backend**: A **Java-based Spring Boot API** developed with **Maven** and **Java 17**, using **Spring Security** and **JWT** for authentication. The backend facilitates communication between the IoT system (simulated in Wokwi) and the user portal, and processes the sensor data from the ESP32.
- **Frontend**: A dynamic **web portal** built with **React**, **Vite**, and **SWC** for fast development and efficient bundling. The frontend allows for easy monitoring, control of the system, and displays real-time data from the IoT sensors. The portal interacts with the backend via a **RESTful API**.
- **Database**: A **relational database** (e.g., H2 or MySQL) is used for **storing and managing sensor data**, allowing for analytical reports and data visualization.
- **API**: A **RESTful API** provides real-time communication between the **IoT ecosystem** and the **management portal**, with endpoints secured using JWT tokens. This API handles both data retrieval and device control commands from the frontend.
