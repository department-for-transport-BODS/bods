// Response shapes of transit_odp/timetables/views/line_detail_api.py

export type TimetableObservation = {
  title: string;
  text: string;
  resolve: string;
};

export type TimetableColumn = {
  name: string;
  observation: TimetableObservation | null;
};

export type TimetableStop = {
  name: string;
  atcoCode: string;
  street: string;
  indicator: string;
  stopType: string;
  observation: TimetableObservation | null;
};

export type TimetableCell = {
  departureTime: string;
  journeyId: number | null;
  observations: TimetableObservation[];
};

export type TimetableRow = {
  index: number;
  stop: TimetableStop;
  cells: TimetableCell[];
};

export type TimetableDirection = {
  direction: 'outbound' | 'inbound';
  journeyName: string;
  isEmpty: boolean;
  totalPage: number;
  currPage: number;
  showAll: boolean;
  totalRowCount: number;
  pageParam: string;
  showAllParam: string;
  columns: TimetableColumn[];
  rows: TimetableRow[];
};

export type Timetable = {
  currDate: string;
  isTimetableInfoAvailable: boolean;
  directions: TimetableDirection[];
};

export type ValidFile = {
  filename: string;
  startDate: string | null;
  endDate: string | null;
};

export type BookingMethods = {
  phone: string | null;
  email: string | null;
  url: string | null;
};

export type LineDetail = {
  revisionId: number;
  lineName: string;
  serviceCode: string;
  serviceType: string;
  currentValidFiles: ValidFile[];
  bookingArrangements: string | null;
  bookingMethods: BookingMethods | null;
  timetable: Timetable | null;
};

export type PublishLineDetail = LineDetail & {
  orgId: number;
  datasetId: number;
  feedName: string;
};

export type DataLineDetail = LineDetail & {
  datasetId: number;
  datasetName: string;
};
