CREATE DATABASE IF NOT EXISTS FLASK_FORUM;

USE FLASK_FORUM;

CREATE TABLE IF NOT EXISTS USERS(
  ID INT NOT NULL AUTO_INCREMENT,
  USERNAME VARCHAR(20),
  EMAIL VARCHAR(60),
  PASSWORD_HASH CHAR(64) NOT NULL,
  SALT CHAR(16) NOT NULL,
  CREATION_DATE TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  ISADMIN BOOL DEFAULT FALSE,
  PRIMARY KEY(ID)
);

CREATE TABLE IF NOT EXISTS TOPICS(
  ID INT NOT NULL AUTO_INCREMENT,
  NAME VARCHAR(50),
  CREATORID INT,
  CREATION_DATE TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  ISPINNED BOOL DEFAULT FALSE,
  PRIMARY KEY(ID),
  FOREIGN KEY(CREATORID) REFERENCES USERS(ID)
);

CREATE TABLE IF NOT EXISTS POSTS(
  ID INT NOT NULL AUTO_INCREMENT,
  CONTENT TEXT,
  CREATORID INT,
  TOPICID INT,
  CREATION_DATE TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  PRIMARY KEY(ID),
  FOREIGN KEY(CREATORID) REFERENCES USERS(ID),
  FOREIGN KEY(TOPICID) REFERENCES TOPICS(ID)
)