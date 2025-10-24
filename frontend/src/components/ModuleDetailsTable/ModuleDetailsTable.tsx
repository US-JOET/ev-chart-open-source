/**
 * Table containing the details of a single module. Imported into the Module Details view.
 * @packageDocumentation
 **/
import React, { useState } from "react";

import { Button, Grid, GridContainer, Icon, Pagination, Select, Table } from "evchartstorybook";

import { ModuleTwoDatum, ModuleTwoHeaders } from "../../interfaces/ModuleData/module-two-interface";
import { ModuleThreeDatum, ModuleThreeHeaders } from "../../interfaces/ModuleData/module-three-interface";
import { ModuleFourDatum, ModuleFourHeaders } from "../../interfaces/ModuleData/module-four-interface";
import { ModuleFiveDatum, ModuleFiveHeaders } from "../../interfaces/ModuleData/module-five-interface";
import { ModuleSixDatum, ModuleSixHeaders } from "../../interfaces/ModuleData/module-six-interface";
import { ModuleSevenDatum, ModuleSevenHeaders } from "../../interfaces/ModuleData/module-seven-interface";
import { ModuleEightDatum, ModuleEightHeaders } from "../../interfaces/ModuleData/module-eight-interface";
import { ModuleNineDatum, ModuleNineHeaders } from "../../interfaces/ModuleData/module-nine-interface";

import "./ModuleDetailsTable.css";

/**
 * Interface defining the props that are passed to the ModuleDetailsTable component
 */
interface ModuleDetailsTableProps {
  /**
   * The header text based the module selected
   */
  moduleHeaders:
    | undefined
    | ModuleTwoHeaders
    | ModuleThreeHeaders
    | ModuleFourHeaders
    | ModuleFiveHeaders
    | ModuleSixHeaders
    | ModuleSevenHeaders
    | ModuleEightHeaders
    | ModuleNineHeaders;
  /**
   * The data based the module selected
   */
  moduleData:
    | undefined
    | Array<ModuleTwoDatum>
    | Array<ModuleThreeDatum>
    | Array<ModuleFourDatum>
    | Array<ModuleFiveDatum>
    | Array<ModuleSixDatum>
    | Array<ModuleSevenDatum>
    | Array<ModuleEightDatum>
    | Array<ModuleNineDatum>;
  /**
   * Function to open the CSV download modal
   */
  openCSVModal?: () => void;
}

/**
 * ModuleDetailsTable
 * Table data shown on the Modules Details page
 * @returns the react component with the table information
 */
export const ModuleDetailsTable: React.FC<ModuleDetailsTableProps> = ({
  moduleHeaders,
  moduleData,
  openCSVModal,
}): React.ReactElement => {
  /**
   * Manage pagination
   */
  const [current, setCurrentPage] = useState<number>(1);
  const [itemsPerPage, setItemsPerPage] = useState<number>(25);

  const numberOfPages = moduleData !== undefined ? Math.ceil(moduleData.length / itemsPerPage) : 0;
  const totalItems = moduleData !== undefined ? moduleData.length : 0;

  const startIndex = (Number(current) - 1) * Number(itemsPerPage);
  const endIndex = Number(startIndex) + Number(itemsPerPage);
  const visibleData = moduleData !== undefined ? moduleData.slice(startIndex, endIndex) : [];

  /**
   * Handle user selecting the 'Next' paginated page.
   * Increments the current page number by one.
   */
  const handleNext = () => {
    const nextPage = current + 1;
    setCurrentPage(nextPage);
  };

  /**
   * Handle user selecting the 'Previous' paginated page.
   * Decrements the current page number by one.
   */
  const handlePrevious = () => {
    const prevPage = current - 1;
    setCurrentPage(prevPage);
  };

  /**
   * Handle user moving between paginated pages
   * @param event html mouse event
   * @param pageNum the selected page number
   */
  const handlePageNumber = (event: React.MouseEvent<HTMLButtonElement>, pageNum: number) => {
    setCurrentPage(pageNum);
  };

  /**
   * Update the number of pages based on user selection
   * @param event the selected number of items per page
   */
  const updateNumPages = (event: any) => {
    setItemsPerPage(event);
    setCurrentPage(1);
  };

  return (
    <div id="moduleDetailsTable">
      <GridContainer className="pagination-info">
        <Grid row className="module-details-table-info">
          {moduleData !== undefined && moduleData.length > 10 ? (
            <div className="pagination-info-row">
              <p className="pagination-info-row-count">
                {startIndex + 1}-{endIndex > totalItems ? totalItems : endIndex} of {totalItems} rows
              </p>
              <p className="pagination-info-row-per-page">Rows per page:</p>
              <Select
                id="moduleDetailsSelectItemsPerPage"
                name="module-details-select-items-per-page"
                title="module-details-select-items-per-page"
                style={{ width: 90 }}
                value={itemsPerPage}
                onChange={(e) => updateNumPages(e.target.value)}
              >
                <option value="10">10</option>
                <option value="25">25</option>
                <option value="50">50</option>
                <option value="100">100</option>
              </Select>
            </div>
          ) : (
            <div className="pagination-info-row" />
          )}
          <div className="module-details-button-group">
            <Button
              type="button"
              unstyled
              id="downloadAsCSVButton"
              className="module-details-unstyled-button"
              onClick={openCSVModal}
            >
              <p>Download as CSV</p>
            </Button>
            <Button
              type="button"
              unstyled
              id="openPDFButton"
              className="module-details-unstyled-button"
              onClick={() => window.open("https://driveelectric.gov/files/ev-chart-data-guidance.pdf", "_blank")}
            >
              <p>
                <Icon.Launch className="pdf-launch-icon" />
                Data Format and Preparation Guidance
              </p>
            </Button>
          </div>
        </Grid>
      </GridContainer>
      <Table striped={true} fixed={true} fullWidth={true}>
        <thead>
          <tr>
            {moduleHeaders !== undefined &&
              Object.entries(moduleHeaders).map(([headerValue, headerName]) => {
                return (
                  <th colSpan={1} scope="colgroup" className="text-left" key={headerValue}>
                    {headerName}
                  </th>
                );
              })}
          </tr>
        </thead>
        <tbody>
          {moduleData !== undefined &&
            visibleData.map((datum: any, index: number) => {
              return (
                <tr key={index}>
                  {moduleHeaders !== undefined &&
                    Object.entries(moduleHeaders).map(([headerValue]) => {
                      return (
                        <td className="text-left overflow-ellipsis-details-data" key={headerValue}>
                          {datum[headerValue] === null ||
                          datum[headerValue] === ""
                            ? "-"
                            : datum[headerValue]}
                        </td>
                      );
                    })}
                </tr>
              );
            })}
        </tbody>
      </Table>
      {moduleData !== undefined && moduleData.length > 10 && (
        <GridContainer>
          <Grid row style={{ justifyContent: "center" }}>
            <Pagination
              totalPages={numberOfPages}
              pathname="module/:uploadID"
              currentPage={current}
              onClickNext={handleNext}
              onClickPrevious={handlePrevious}
              onClickPageNumber={handlePageNumber}
            />
          </Grid>
        </GridContainer>
      )}
    </div>
  );
};

export default ModuleDetailsTable;
