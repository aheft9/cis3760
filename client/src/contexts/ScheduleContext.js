import React, { useState, createContext } from 'react';

export const ScheduleContext = createContext({});

export const ScheduleContextProvider = (props) => {
  const [schedule, setSchedule] = useState([]);
  const [semesters, setSemesters] = useState([]);
  const [currentSem, setCurrentSem] = useState(0);

  const getSchedule = () => {
    return schedule.filter((section) => section.sem === semesters[currentSem].sem);
  };

  const convertTime = (str) => {
    let [hours, minutes] = str.split(':');
    const modifier = minutes.slice(-2);
    minutes = minutes.replace('AM', '');
    minutes = minutes.replace('PM', '');

    if (hours === '12') {
      hours = '00';
    }

    if (modifier === 'PM') {
      hours = parseInt(hours) + 12;
    }

    return `${hours}:${minutes}:00`;
  };

  const getMeetingTimes = (meeting) => {
    const today = new Date().toJSON().slice(0, 10);

    const start = new Date(`${today}T${convertTime(meeting.start_time)}`);
    const end = new Date(`${today}T${convertTime(meeting.end_time)}`);

    return [start, end];
  };

  const isInvalidMeeting = (meeting) => {
    if (meeting.meeting_type === 'EXAM') return true;
    if (meeting.meeting_type === 'Distance') return true;
    if (meeting.meeting_day.includes('TBA')) return true;

    return false;
  };

  const addSection = (section) => {
    setSchedule([...schedule, section]);
  };

  const removeSection = (sectionNum) => {
    setSchedule(schedule.filter((s) => s.num !== sectionNum));
  };

  const isConflict = (section) => {
    for (let meeting of section.meeting) {
      if (isInvalidMeeting(meeting)) continue;

      const [start, end] = getMeetingTimes(meeting);

      for (let sSection of schedule) {
        if (sSection.num === section.num) continue;

        for (let sMeeting of sSection.meeting) {
          if (isInvalidMeeting(sMeeting)) continue;

          const [sStart, sEnd] = getMeetingTimes(sMeeting);

          // check time intersection
          if ((start >= sStart && start <= sEnd) || (end >= sStart && end <= sEnd)) {
            // check date intersection
            const days = meeting.meeting_day.split(',');
            const sDays = sMeeting.meeting_day.split(',');

            if (days.some((day) => sDays.includes(day))) {
              return true;
            }
          }
        }
      }
    }

    return false;
  };

  return (
    <ScheduleContext.Provider value={{ getSchedule, schedule, semesters, setSemesters, currentSem, setCurrentSem, addSection, removeSection, isConflict }}>
      {props.children}
    </ScheduleContext.Provider>
  );
};
