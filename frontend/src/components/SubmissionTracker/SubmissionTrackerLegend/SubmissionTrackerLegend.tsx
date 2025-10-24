/**
 * Legend for the icons in the Submission Tracker table.
 * @packageDocumentation
 **/
import React, { useState } from "react";

import { Button, GridContainer, Grid, Icon } from "evchartstorybook";

import SubmissionTrackerModal from "../../Modals/SubmissionTrackerModal/SubmissionTrackerModal";

import "./SubmissionTrackerLegend.css";

interface LegendItem {
  /**
   * Unique key for each item
   */
  id: number;
  /**
   * Icon indicating the status of the modules in the reporting period
   */
  icon: React.ReactNode;
  /**
   * Label describing the status of the modules in the reporting period
   */
  description: string;
}

export const SubmissionTrackerLegend: React.FC = (): React.ReactElement => {
  const [isSubmissionTrackerModalOpen, setIsSubmissionTrackerModalOpen] = useState(false);

  /**
   * Function to open the Submission Tracker Guidance modal
   */
  const openSubmissionTrackerModal = () => {
    setIsSubmissionTrackerModalOpen(true);
  };

  /**
   * Function to close the Submission Tracker Guidance modal
   */
  const closeSubmissionTrackerModal = () => {
    setIsSubmissionTrackerModalOpen(false);
  };

  /**
   * Items to be displayed in the legend.
   * Includes an icon and description.
   */
  const legendItems: LegendItem[] = [
    {
      id: 1,
      icon: <Icon.TrackerBallAttention size={3} className="st-modal" />,
      description: "Module(s) require attention/review",
    },
    {
      id: 2,
      icon: <Icon.TrackerBallSubmitted size={3} className="st-modal icon-overflow-visible" />,
      description: "Approved/submitted data for all modules",
    },
    {
      id: 3,
      icon: <Icon.TrackerBallPartialData size={3} className="st-modal icon-overflow-visible" />,
      description: "Some modules approved/submitted",
    },
    {
      id: 4,
      icon: <Icon.TrackerBallNoData size={3} className="st-modal icon-overflow-visible" />,
      description: "No modules approved/submitted",
    },
    {
      id: 5,
      icon: <Icon.TrackerBallNoDataRequired size={3} className="st-modal" />,
      description: "No modules due yet",
    },
    {
      id: 6,
      icon: <Icon.TrackerBallNoDataRequiredEver size={3} className="st-modal" />,
      description: "Station not operational, no submissions required",
    },
  ];

  return (
    <>
      <div className="submission-tracker-outline" id="SubmissionTrackerLegend" data-testid="SubmissionTrackerLegend">
        <GridContainer>
          <Grid row>
            <h2 className="legend-line submission-tracker-legend-title">
              <span> Submission Tracker Key </span>
            </h2>
          </Grid>
          <Grid row>
            {legendItems.map((item) => (
              <Grid key={item.id} tablet={{ col: 4 }} className="legend-item">
                <div className="icon">{item.icon}</div>
                <div className="icon-description">{item.description}</div>
              </Grid>
            ))}
          </Grid>
        </GridContainer>
      </div>
      <Button type="button" unstyled id="submissionTrackerModalButton" onClick={openSubmissionTrackerModal}>
        <p className="submission-tracker-unstyled-button-text">View submission tracker guidance</p>
      </Button>

      {isSubmissionTrackerModalOpen && <SubmissionTrackerModal onClose={closeSubmissionTrackerModal} />}
    </>
  );
};

export default SubmissionTrackerLegend;
