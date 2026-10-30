/**
 * `/timetable/` is Django's public URL for the timetables data browser
 * (`search` in transit_odp/browse/urls/root.py), which operator pages link to.
 * Next.js serves the same page under `/timetables`, so alias it here.
 */
export { default } from '../timetables/page';
