import 'server-only';

function isOn(envVar: string): boolean {
  return process.env[envVar]?.trim().toLowerCase() === 'true';
}

export const featureFlags = {
  dqsRequireAttention: isOn('FEATURE_FLAG_DQS_REQUIRE_ATTENTION'),
  dqsRequireAttentionComplianceReportActive: isOn('FEATURE_FLAG_DQS_REQUIRE_ATTENTION_COMPLIANCE_REPORT_ACTIVE'),
  extractTracksData: isOn('FEATURE_FLAG_EXTRACT_TRACKS_DATA'),
  isAvlConsumerSubsActive: isOn('FEATURE_FLAG_IS_AVL_CONSUMER_SUBS_ACTIVE'),
  isAvlRequireAttentionActive: isOn('FEATURE_FLAG_IS_AVL_REQUIRE_ATTENTION_ACTIVE'),
  isCancellationLogicActive: isOn('FEATURE_FLAG_IS_CANCELLATION_LOGIC_ACTIVE'),
  isCancellationsLive: isOn('FEATURE_FLAG_IS_CANCELLATIONS_LIVE'),
  isCompleteServicePagesActive: isOn('FEATURE_FLAG_IS_COMPLETE_SERVICE_PAGES_ACTIVE'),
  isCompleteServicePagesRealTimeDataActive: isOn('FEATURE_FLAG_IS_COMPLETE_SERVICE_PAGES_REAL_TIME_DATA_ACTIVE'),
  isCreateSevenDayPpcReportDaily: isOn('FEATURE_FLAG_IS_CREATE_SEVEN_DAY_PPC_REPORT_DAILY'),
  isFaresCappingRuleValidationEnabled: isOn('FEATURE_FLAG_IS_FARES_CAPPING_RULE_VALIDATION_ENABLED'),
  isFaresRequireAttentionActive: isOn('FEATURE_FLAG_IS_FARES_REQUIRE_ATTENTION_ACTIVE'),
  isFaresRequireAttentionComplianceReportActive: isOn('FEATURE_FLAG_IS_FARES_REQUIRE_ATTENTION_COMPLIANCE_REPORT_ACTIVE'),
  isFaresServerlessPublishingActive: isOn('FEATURE_FLAG_IS_FARES_SERVERLESS_PUBLISHING_ACTIVE'),
  isFaresValidatorActive: isOn('FEATURE_FLAG_IS_FARES_VALIDATOR_ACTIVE'),
  isFranchiseOrganisationActive: isOn('FEATURE_FLAG_IS_FRANCHISE_ORGANISATION_ACTIVE'),
  isGtfsServiceAlertsLive: isOn('FEATURE_FLAG_IS_GTFS_SERVICE_ALERTS_LIVE'),
  isNewDataQualityServiceActive: isOn('FEATURE_FLAG_IS_NEW_DATA_QUALITY_SERVICE_ACTIVE'),
  isNewGtfsApiActive: isOn('FEATURE_FLAG_IS_NEW_GTFS_API_ACTIVE'),
  isOperatorPrefetchSraActive: isOn('FEATURE_FLAG_IS_OPERATOR_PREFETCH_SRA_ACTIVE'),
  isPrefetchDbComplianceReportActive: isOn('FEATURE_FLAG_IS_PREFETCH_DB_COMPLIANCE_REPORT_ACTIVE'),
  isServerlessPublishingActive: isOn('FEATURE_FLAG_IS_SERVERLESS_PUBLISHING_ACTIVE'),
  isSpecialDaysPpcLogicActive: isOn('FEATURE_FLAG_IS_SPECIAL_DAYS_PPC_LOGIC_ACTIVE'),
  isSpecificFeedback: isOn('FEATURE_FLAG_IS_SPECIFIC_FEEDBACK'),
  isSplitRegistrationLogicActive: isOn('FEATURE_FLAG_IS_SPLIT_REGISTRATION_LOGIC_ACTIVE'),
  isTimetableVisualiserActive: isOn('FEATURE_FLAG_IS_TIMETABLE_VISUALISER_ACTIVE'),
  isUiltaPrefetchSraActive: isOn('FEATURE_FLAG_IS_UILTA_PREFETCH_SRA_ACTIVE'),
  isUsingStepFunctionForDqs: isOn('FEATURE_FLAG_IS_USING_STEP_FUNCTION_FOR_DQS'),
} as const;
