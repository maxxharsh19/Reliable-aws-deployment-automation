# Reliable AWS Deployment Automation

An end-to-end DevOps project that automates application testing, Docker image creation, Amazon ECR publishing, and deployment to an AWS EC2 instance using GitHub Actions, OIDC, and AWS Systems Manager.

## Project Overview

This project demonstrates an automated CI/CD pipeline for a Python-based Deployment Health & Status API.

A code push to the master branch triggers automated tests, builds a Docker image, publishes it to Amazon ECR, and deploys it to an EC2 instance through AWS Systems Manager.

## Architecture

```mermaid
flowchart TD
    A[Developer Push to GitHub] --> B[GitHub Actions]
    B --> C[Python Unit Tests]
    C --> D[Configure AWS Credentials using OIDC]
    D --> E[Build Docker Image]
    E --> F[Amazon ECR]
    F --> G[AWS Systems Manager]
    G --> H[EC2 Ubuntu Instance]
    H --> I[Docker Container]
    I --> J[Deployment Health API]
    K[Terraform] --> H
    L[Ansible] --> H
    J --> M[HTTP Health Check]
