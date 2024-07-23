DROP DATABASE IF EXISTS SCHOOL;
CREATE DATABASE SCHOOL;
Use SCHOOL;

CREATE TABLE Account
(
	User_ID VARCHAR(50) PRIMARY KEY,
  Password VARCHAR(128),
  Type 	ENUM ("Admin", "Student", "Lecturer")
);

CREATE TABLE Student
(
	StudentID VARCHAR(50) PRIMARY KEY,
	FirstName VARCHAR(50),
  MiddleName VARCHAR(50),
  LastName	VARCHAR(50),
  User_ID VARCHAR(50),
  FOREIGN KEY(User_ID) REFERENCES Account(User_ID)
);

CREATE TABLE Admin
(
	AdminID VARCHAR(50) PRIMARY KEY,
	FirstName VARCHAR(50),
  MiddleName VARCHAR(50),
  LastName	VARCHAR(50),
  User_ID VARCHAR(50),
  FOREIGN KEY(User_ID) REFERENCES Account(User_ID)
);

CREATE TABLE `forum` (
  `forum_id` int(11) NOT NULL AUTO_INCREMENT,
  `c_id` varchar(50) DEFAULT NULL,
  `title` varchar(50) DEFAULT NULL,
  `datecreated` date DEFAULT NULL,
  `description` varchar(500) DEFAULT NULL,
  PRIMARY KEY (`forum_id`)
) ;

CREATE TABLE `discussion_thread` (
  `disc_id` int(11) NOT NULL AUTO_INCREMENT,
  `forum_id` int(11) DEFAULT NULL,
  `title` varchar(50) DEFAULT NULL,
  `datecreated` date DEFAULT NULL,
  `message` varchar(500) DEFAULT NULL,
  `owner` varchar(50) DEFAULT NULL,
  `reply_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`disc_id`)
);

CREATE TABLE Lecturer
(
	l_id VARCHAR(50) PRIMARY KEY,
	FirstName VARCHAR(50),
  MiddleName VARCHAR(50),
  LastName	VARCHAR(50),
  User_ID VARCHAR(50),
  FOREIGN KEY(User_ID) REFERENCES Account(User_ID)
);

CREATE TABLE Register
(
	User_ID VARCHAR(50),
  Mem_ID VARCHAR(50),
  DateCreated date,
  primary key (User_ID, Mem_ID)
);

CREATE TABLE assigned (
  c_id varchar(50) DEFAULT NULL,
  l_id varchar(50) NOT NULL,
  PRIMARY KEY (c_id)
);

CREATE TABLE StudentCourseReg
(
	c_id VARCHAR(50),
  StudentID VARCHAR(50),
  primary key (c_id, StudentID)
);

CREATE TABLE Course
(
	CourseID VARCHAR(50) PRIMARY KEY,
	Title VARCHAR(50),
  Credits int
);

CREATE TABLE Calendar
(
	CalID int PRIMARY KEY AUTO_INCREMENT ,
	c_id VARCHAR(50)
);

CREATE TABLE calendarev (
  CalID int(11) DEFAULT NULL,
  EventName varchar(50) NOT NULL,
  DueDate varchar(50) DEFAULT NULL,
  PRIMARY KEY (CalID, EventName)
);

CREATE TABLE `content` (
  `cont_id` int(11) NOT NULL AUTO_INCREMENT,
  `c_id` varchar(50) DEFAULT NULL,
  `title` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`cont_id`)
);

CREATE TABLE `contentitems` (
  `item_id` int(11) NOT NULL AUTO_INCREMENT,
  `cont_id` int(11) DEFAULT NULL,
  `title` varchar(50) DEFAULT NULL,
  `link_filepath` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`item_id`)
);

CREATE TABLE assignment (
  ass_id int(11) NOT NULL AUTO_INCREMENT,
  CourseID VARCHAR(50),
  stud_id VARCHAR(50) DEFAULT NULL,
  files varchar(50) DEFAULT NULL,
  dateSubmitted date DEFAULT NULL,
  grade int(11) DEFAULT NULL,
  PRIMARY KEY (ass_id)
); 

INSERT INTO Admin(AdminID, FirstName, MiddleName, LastName) VALUES ("Ranaldo1", "Ranaldo", "Chad", "Green");
INSERT INTO Admin(AdminID, FirstName, MiddleName, LastName) VALUES ("Steph1", "Stephanie", "Knight", "Allen");

INSERT INTO Lecturer(l_id, FirstName, MiddleName, LastName) VALUES ("Sheamar1", "Shemar", "AJ", "White");

INSERT INTO Student(StudentID, FirstName, MiddleName, LastName) VALUES ("Kareem1", "Kareem", "Trevor", "Pingue");
INSERT INTO Student(StudentID, FirstName, MiddleName, LastName) VALUES ("Kylos1", "Kyle", "Timothy", "Grant");