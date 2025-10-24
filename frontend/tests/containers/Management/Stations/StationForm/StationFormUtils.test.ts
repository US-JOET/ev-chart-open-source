import { describe, it, expect, vi } from "vitest";

import { portValidation, checkValidData } from "../../../../../src/containers/Management/Stations/StationForm/StationFormUtils";
import { StationAddNew } from "../../../../../src/interfaces/Stations/stations-interface";
import * as utils from "../../../../../src/utils/getJWTInfo";

vi.spyOn(utils, "getOrgID");

const updatedMissingRequiredMessage = {
    nickname: false,
    address: false,
    city: false,
    project_type: false,
    network_provider: false,
    station_id: false,
    latitude: false,
    longitude: false,
    num_fed_funded_ports: false,
    num_non_fed_funded_ports: false,
    state: false,
    authorized_subrecipients: false,
    zip: false,
    zip_extended: false,
    fed_funded_ports: false,
    non_fed_funded_ports: false,
    dr_id: false,
  };

const updatedCustomErrors = {
    station_id: false,
    latitude: false,
    longitude: false,
    num_fed_funded_ports: false,
    num_non_fed_funded_ports: false,
    zip: false,
    zip_extended: false,
    fed_funded_ports: false,
    non_fed_funded_ports: false,
    authorized_subrecipients: false,
    num_fed_funded_ports_zero: false,
    num_fed_funded_ports_less_than: false,
    num_fed_funded_ports_greater_than: false,
    num_non_fed_funded_ports_zero: false,
    num_non_fed_funded_ports_less_than: false,
    num_non_fed_funded_ports_greater_than: false,
}
const updatedinvalidField = {
    nickname: false,
    address: false,
    city: false,
    project_type: false,
    network_provider: false,
    station_id: false,
    latitude: false,
    longitude: false,
    num_fed_funded_ports: false,
    num_non_fed_funded_ports: false,
    state: false,
    authorized_subrecipients: false,
    zip: false,
    zip_extended: false,
    fed_funded_ports: false,
    non_fed_funded_ports: false,
    dr_id: false,
  };

const stationValues = <StationAddNew><unknown>{
  address: "",
  city: "",
  project_type: "",
  station_id: "",
  latitude: "",
  longitude: "",
  nickname: "",
  num_fed_funded_ports: null,
  num_non_fed_funded_ports: null,
  state: "undefined",
  status: "Active",
  network_provider: "",
  operational_date: "",
  NEVI: 0,
  CFI: 0,
  EVC_RAA: 0,
  CMAQ: 0,
  CRP: 0,
  OTHER: 0,
  AFC: undefined,
  federally_funded: null,
  authorized_subrecipients: [],
  zip: "",
  zip_extended: "",
  fed_funded_ports: [],
  non_fed_funded_ports: [],
  dr_id: vi.spyOn(utils, "getOrgID").mockReturnValue("111"),
}


describe("portValidation() - number of federal funded ports as a requried field", () => {
  it('should handle the case where the number of federal funded ports was not provided and no ports were listed', () => {
    const invalidStationValues = {...stationValues}
    invalidStationValues["num_fed_funded_ports"] = null

    const mock_set_incorrect_values = vi.fn()
    portValidation(
        true,
        "num_fed_funded_ports",
        "fed_funded_ports",
        invalidStationValues,
        updatedCustomErrors,
        updatedinvalidField,
        updatedMissingRequiredMessage,
        mock_set_incorrect_values
    );

    expect(updatedMissingRequiredMessage.num_fed_funded_ports).toBe(true)
    // since no value was provided, there should be no custom errors set to true
    Object.values(updatedCustomErrors).forEach((value) => {
      expect(value).toBe(false)
    })

    Object.entries(updatedinvalidField).forEach(([key,value]) => {
      if (key === "num_fed_funded_ports"){
        expect(value).toBe(true)
      }
      else {
        expect(value).toBe(false)
      }
    })

    Object.entries(updatedMissingRequiredMessage).forEach(([key,value]) => {
      if (key === "num_fed_funded_ports"){
        expect(value).toBe(true)
      }
      else {
        expect(value).toBe(false)
      }
    })

  });


  it('should handle the case where the number of federal funded ports is 0 and no ports listed', () => {
    const invalidStationValues = {...stationValues}
    invalidStationValues["num_fed_funded_ports"] = 0

    const mock_set_incorrect_values = vi.fn()
    portValidation(
        true,
        "num_fed_funded_ports",
        "fed_funded_ports",
        invalidStationValues,
        updatedCustomErrors,
        updatedinvalidField,
        updatedMissingRequiredMessage,
        mock_set_incorrect_values
    );

    Object.entries(updatedCustomErrors).forEach(([key,value]) => {
      if (key === "num_fed_funded_ports_zero"){
        expect(value).toBe(true)
      }
      else {
        expect(value).toBe(false)
      }
    })

    Object.entries(updatedinvalidField).forEach(([key,value]) => {
      if (key === "num_fed_funded_ports"){
        expect(value).toBe(true)
      }
      else {
        expect(value).toBe(false)
      }
    })

    Object.values(updatedMissingRequiredMessage).forEach((value) => {
      expect(value).toBe(false)
    })
  });


  it('should handle the case where the number of federal funded ports is 0 and ports are listed', () => {
    const invalidStationValues = {...stationValues}
    invalidStationValues["num_fed_funded_ports"] = 0
    invalidStationValues["fed_funded_ports"] = [
      {
        "port_id":"11",
        "port_type":""
      }
    ]

    const mock_set_incorrect_values = vi.fn()
    portValidation(
        true,
        "num_fed_funded_ports",
        "fed_funded_ports",
        invalidStationValues,
        updatedCustomErrors,
        updatedinvalidField,
        updatedMissingRequiredMessage,
        mock_set_incorrect_values
    );

    Object.entries(updatedCustomErrors).forEach(([key,value]) => {
      if (key === "num_fed_funded_ports_zero"){
        expect(value).toBe(true)
      }
      else {
        expect(value).toBe(false)
      }
    })

    Object.entries(updatedinvalidField).forEach(([key,value]) => {
      if (key === "num_fed_funded_ports"){
        expect(value).toBe(true)
      }
      else {
        expect(value).toBe(false)
      }
    })

    Object.values(updatedMissingRequiredMessage).forEach((value) => {
      expect(value).toBe(false)
    })
  });


  it('should handle the case where the number of federal funded ports is greater than the federal ports provided', () => {

    const invalidStationValues = {...stationValues}
    invalidStationValues["num_fed_funded_ports"] = 1

    const mock_set_incorrect_values = vi.fn()
    portValidation(
        true,
        "num_fed_funded_ports",
        "fed_funded_ports",
        invalidStationValues,
        updatedCustomErrors,
        updatedinvalidField,
        updatedMissingRequiredMessage,
        mock_set_incorrect_values
    );

    Object.entries(updatedCustomErrors).forEach(([key,value]) => {
      if (key === "num_fed_funded_ports_greater_than"){
        expect(value).toBe(true)
      }
      else {
        expect(value).toBe(false)
      }
    })

    Object.entries(updatedinvalidField).forEach(([key,value]) => {
      if (key === "num_fed_funded_ports"){
        expect(value).toBe(true)
      }
      else {
        expect(value).toBe(false)
      }
    })

    Object.values(updatedMissingRequiredMessage).forEach((value) => {
      expect(value).toBe(false)
    })

  });


  it('should handle the case where the number of federal funded ports is less than the federal ports provided', () => {

    const invalidStationValues = {...stationValues}
    invalidStationValues["num_fed_funded_ports"] = 1
    invalidStationValues["fed_funded_ports"] = [
      {
        "port_id":"123",
        "port_type":"DCFC"
      },
      {
        "port_id":"1234",
        "port_type":"DCFC"
      }
    ]

    const mock_set_incorrect_values = vi.fn()
    portValidation(
        true,
        "num_fed_funded_ports",
        "fed_funded_ports",
        invalidStationValues,
        updatedCustomErrors,
        updatedinvalidField,
        updatedMissingRequiredMessage,
        mock_set_incorrect_values
    );

    Object.entries(updatedCustomErrors).forEach(([key,value]) => {
      if (key === "num_fed_funded_ports_less_than"){
        expect(value).toBe(true)
      }
      else {
        expect(value).toBe(false)
      }
    })

    Object.entries(updatedinvalidField).forEach(([key,value]) => {
      if (key === "num_fed_funded_ports"){
        expect(value).toBe(true)
      }
      else {
        expect(value).toBe(false)
      }
    })

    Object.values(updatedMissingRequiredMessage).forEach((value) => {
      expect(value).toBe(false)
    })
  });

  it('should handle the case where the number of federal funded ports is null, but federal ports are listed', () => {
    const invalidStationValues = {...stationValues}
    invalidStationValues["num_fed_funded_ports"] = null
    invalidStationValues["fed_funded_ports"] = [
      {
        "port_id":"11",
        "port_type":""
      }
    ]
    const mock_set_incorrect_values = vi.fn()
    portValidation(
        true,
        "num_fed_funded_ports",
        "fed_funded_ports",
        invalidStationValues,
        updatedCustomErrors,
        updatedinvalidField,
        updatedMissingRequiredMessage,
        mock_set_incorrect_values
    );

    Object.values(updatedCustomErrors).forEach((value)=> {
      expect(value).toBe(false)
    })
    Object.entries(updatedinvalidField).forEach(([key,value]) => {
      if (key === "num_fed_funded_ports"){
        expect(value).toBe(true)
      }
      else {
        expect(value).toBe(false)
      }
    })
    Object.entries(updatedMissingRequiredMessage).forEach(([key,value]) => {
      if (key === "num_fed_funded_ports"){
        expect(value).toBe(true)
      }
      else {
        expect(value).toBe(false)
      }
    })
  });


  it('should handle the happy path case where the number of federal funded ports equals the ports provided', () => {
    const validStationValues = {...stationValues}
    validStationValues["num_fed_funded_ports"] = 1
    validStationValues["fed_funded_ports"] = [
      {
        "port_id": "123",
        "port_type": "LC"
      }
    ]

    const mock_set_incorrect_values = vi.fn()
    portValidation(
        true,
        "num_fed_funded_ports",
        "fed_funded_ports",
        validStationValues,
        updatedCustomErrors,
        updatedinvalidField,
        updatedMissingRequiredMessage,
        mock_set_incorrect_values
    );

    // verifies that all attributes are set to false for the custom errors, invalid field, and missing required objects
    Object.values(updatedCustomErrors).forEach((value)=> {
      expect(value).toBe(false)
    })
    Object.values(updatedinvalidField).forEach((value)=> {
      expect(value).toBe(false)
    })
    Object.values(updatedMissingRequiredMessage).forEach((value)=> {
      expect(value).toBe(false)
    })
  });

})


describe("portValidation() - number of non-federal funded ports as an optional field", () => {
  it('should handle the happy path case where the number of non federal funded ports is not provided and no ports listed', () => {
    const validStationValues = {...stationValues}
    validStationValues["num_non_fed_funded_ports"] = null
    validStationValues["non_fed_funded_ports"] = []
    const mock_set_incorrect_values = vi.fn()
    portValidation(
        false,
        "num_non_fed_funded_ports",
        "non_fed_funded_ports",
        validStationValues,
        updatedCustomErrors,
        updatedinvalidField,
        updatedMissingRequiredMessage,
        mock_set_incorrect_values
    );

    // verifies that all attributes are set to false for the custom errors, invalid field, and missing required objects
    Object.values(updatedCustomErrors).forEach((value)=> {
      expect(value).toBe(false)
    })
    Object.values(updatedinvalidField).forEach((value)=> {
      expect(value).toBe(false)
    })
    Object.values(updatedMissingRequiredMessage).forEach((value)=> {
      expect(value).toBe(false)
    })
  });


  it('should handle the happy path case where the number of non federal funded ports is 0 and no ports provided', () => {
    const validStationValues = {...stationValues}
    validStationValues["num_non_fed_funded_ports"] = 0
    const mock_set_incorrect_values = vi.fn()
    portValidation(
        false,
        "num_non_fed_funded_ports",
        "non_fed_funded_ports",
        validStationValues,
        updatedCustomErrors,
        updatedinvalidField,
        updatedMissingRequiredMessage,
        mock_set_incorrect_values
    );

    // verifies that all attributes are set to false for the custom errors, invalid field, and missing required objects
    Object.values(updatedCustomErrors).forEach((value)=> {
      expect(value).toBe(false)
    })
    Object.values(updatedinvalidField).forEach((value)=> {
      expect(value).toBe(false)
    })
    Object.values(updatedMissingRequiredMessage).forEach((value)=> {
      expect(value).toBe(false)
    })
  });


  it('should handle the case where the number of non federal funded ports is 0 and non federal ports are provided', () => {
    const invalidStationValues = {...stationValues}
    invalidStationValues["num_non_fed_funded_ports"] = 0
    invalidStationValues["non_fed_funded_ports"] = [
      {
        "port_id":"11",
        "port_type":""
      }
    ]
    const mock_set_incorrect_values = vi.fn()
    portValidation(
        false,
        "num_non_fed_funded_ports",
        "non_fed_funded_ports",
        invalidStationValues,
        updatedCustomErrors,
        updatedinvalidField,
        updatedMissingRequiredMessage,
        mock_set_incorrect_values
    );

    Object.entries(updatedCustomErrors).forEach(([key,value]) => {
      if (key === "num_non_fed_funded_ports_less_than"){
        expect(value).toBe(true)
      }
      else {
        expect(value).toBe(false)
      }
    })

    Object.entries(updatedinvalidField).forEach(([key,value]) => {
      if (key === "num_non_fed_funded_ports"){
        expect(value).toBe(true)
      }
      else {
        expect(value).toBe(false)
      }
    })

    Object.values(updatedMissingRequiredMessage).forEach((value) => {
      expect(value).toBe(false)
    })
  });


  it('should handle the happy path case where the number of non federal funded ports is equal ports provided', () => {
    const validStationValues = {...stationValues}
    validStationValues["num_non_fed_funded_ports"] = 1
    validStationValues["non_fed_funded_ports"] = [
      {
        "port_id":"11",
        "port_type":""
      }
    ]
    const mock_set_incorrect_values = vi.fn()
    portValidation(
        false,
        "num_non_fed_funded_ports",
        "non_fed_funded_ports",
        validStationValues,
        updatedCustomErrors,
        updatedinvalidField,
        updatedMissingRequiredMessage,
        mock_set_incorrect_values
    );

    // verifies that all attributes are set to false for the custom errors, invalid field, and missing required objects
    Object.values(updatedCustomErrors).forEach((value)=> {
      expect(value).toBe(false)
    })
    Object.values(updatedinvalidField).forEach((value)=> {
      expect(value).toBe(false)
    })
    Object.values(updatedMissingRequiredMessage).forEach((value)=> {
      expect(value).toBe(false)
    })
  });


  it('should handle the case where the number of non federal funded ports is greater than non federal ports provided', () => {
    const invalidStationValues = {...stationValues}
    invalidStationValues["num_non_fed_funded_ports"] = 2
    invalidStationValues["non_fed_funded_ports"] = [
      {
        "port_id":"11",
        "port_type":""
      }
    ]
    const mock_set_incorrect_values = vi.fn()
    portValidation(
        false,
        "num_non_fed_funded_ports",
        "non_fed_funded_ports",
        invalidStationValues,
        updatedCustomErrors,
        updatedinvalidField,
        updatedMissingRequiredMessage,
        mock_set_incorrect_values
    );

    Object.entries(updatedCustomErrors).forEach(([key,value]) => {
      if (key === "num_non_fed_funded_ports_greater_than"){
        expect(value).toBe(true)
      }
      else {
        expect(value).toBe(false)
      }
    })

    Object.entries(updatedinvalidField).forEach(([key,value]) => {
      if (key === "num_non_fed_funded_ports"){
        expect(value).toBe(true)
      }
      else {
        expect(value).toBe(false)
      }
    })

    Object.values(updatedMissingRequiredMessage).forEach((value) => {
      expect(value).toBe(false)
    })
  });


  it('should handle the case where the number of non federal funded ports is less than non federal ports provided', () => {
    const invalidStationValues = {...stationValues}
    invalidStationValues["num_non_fed_funded_ports"] = 1
    invalidStationValues["non_fed_funded_ports"] = [
      {
        "port_id":"11",
        "port_type":""
      },
      {
        "port_id":"12",
        "port_type":""
      }
    ]
    const mock_set_incorrect_values = vi.fn()
    portValidation(
        false,
        "num_non_fed_funded_ports",
        "non_fed_funded_ports",
        invalidStationValues,
        updatedCustomErrors,
        updatedinvalidField,
        updatedMissingRequiredMessage,
        mock_set_incorrect_values
    );

    Object.entries(updatedCustomErrors).forEach(([key,value]) => {
      if (key === "num_non_fed_funded_ports_less_than"){
        expect(value).toBe(true)
      }
      else {
        expect(value).toBe(false)
      }
    })

    Object.entries(updatedinvalidField).forEach(([key,value]) => {
      if (key === "num_non_fed_funded_ports"){
        expect(value).toBe(true)
      }
      else {
        expect(value).toBe(false)
      }
    })

    Object.values(updatedMissingRequiredMessage).forEach((value) => {
      expect(value).toBe(false)
    })
  });


  it('should handle the case where the number of non federal funded ports is null, but non federal ports are listed', () => {
    const invalidStationValues = {...stationValues}
    invalidStationValues["num_non_fed_funded_ports"] = null
    invalidStationValues["non_fed_funded_ports"] = [
      {
        "port_id":"11",
        "port_type":""
      }
    ]
    const mock_set_incorrect_values = vi.fn()
    portValidation(
        false,
        "num_non_fed_funded_ports",
        "non_fed_funded_ports",
        invalidStationValues,
        updatedCustomErrors,
        updatedinvalidField,
        updatedMissingRequiredMessage,
        mock_set_incorrect_values
    );

    Object.entries(updatedCustomErrors).forEach(([key,value]) => {
      if (key === "num_non_fed_funded_ports_less_than"){
        expect(value).toBe(true)
      }
      else {
        expect(value).toBe(false)
      }
    })

    Object.entries(updatedinvalidField).forEach(([key,value]) => {
      if (key === "num_non_fed_funded_ports"){
        expect(value).toBe(true)
      }
      else {
        expect(value).toBe(false)
      }
    })

    Object.values(updatedMissingRequiredMessage).forEach((value) => {
      expect(value).toBe(false)
    })
  });

})


describe("portValidation() - number of NON federal funded ports as a requried field", () => {
  it('should handle the case where the number of non federal funded ports was not provided and no ports were listed', () => {
    const invalidStationValues = {...stationValues}
    invalidStationValues["num_non_fed_funded_ports"] = null

    const mock_set_incorrect_values = vi.fn()
    portValidation(
        true,
        "num_non_fed_funded_ports",
        "non_fed_funded_ports",
        invalidStationValues,
        updatedCustomErrors,
        updatedinvalidField,
        updatedMissingRequiredMessage,
        mock_set_incorrect_values
    );

    expect(updatedMissingRequiredMessage.num_non_fed_funded_ports).toBe(true)
    // since no value was provided, there should be no custom errors set to true
    Object.values(updatedCustomErrors).forEach((value) => {
      expect(value).toBe(false)
    })

    Object.entries(updatedinvalidField).forEach(([key,value]) => {
      if (key === "num_non_fed_funded_ports"){
        expect(value).toBe(true)
      }
      else {
        expect(value).toBe(false)
      }
    })

    Object.entries(updatedMissingRequiredMessage).forEach(([key,value]) => {
      if (key === "num_non_fed_funded_ports"){
        expect(value).toBe(true)
      }
      else {
        expect(value).toBe(false)
      }
    })

  });
})


  it('should handle the case where the number of non federal funded ports is 0 and no ports listed', () => {
    const invalidStationValues = {...stationValues}
    invalidStationValues["num_non_fed_funded_ports"] = 0

    const mock_set_incorrect_values = vi.fn()
    portValidation(
        true,
        "num_non_fed_funded_ports",
        "non_fed_funded_ports",
        invalidStationValues,
        updatedCustomErrors,
        updatedinvalidField,
        updatedMissingRequiredMessage,
        mock_set_incorrect_values
    );

    Object.entries(updatedCustomErrors).forEach(([key,value]) => {
      if (key === "num_non_fed_funded_ports_zero"){
        expect(value).toBe(true)
      }
      else {
        expect(value).toBe(false)
      }
    })

    Object.entries(updatedinvalidField).forEach(([key,value]) => {
      if (key === "num_non_fed_funded_ports"){
        expect(value).toBe(true)
      }
      else {
        expect(value).toBe(false)
      }
    })

    Object.values(updatedMissingRequiredMessage).forEach((value) => {
      expect(value).toBe(false)
    })
  });


  it('should handle the case where the number of non federal funded ports is 0 and ports are listed', () => {
    const invalidStationValues = {...stationValues}
    invalidStationValues["num_non_fed_funded_ports"] = 0
    invalidStationValues["non_fed_funded_ports"] = [
      {
        "port_id":"11",
        "port_type":""
      }
    ]

    const mock_set_incorrect_values = vi.fn()
    portValidation(
        true,
        "num_non_fed_funded_ports",
        "non_fed_funded_ports",
        invalidStationValues,
        updatedCustomErrors,
        updatedinvalidField,
        updatedMissingRequiredMessage,
        mock_set_incorrect_values
    );

    Object.entries(updatedCustomErrors).forEach(([key,value]) => {
      if (key === "num_non_fed_funded_ports_zero"){
        expect(value).toBe(true)
      }
      else {
        expect(value).toBe(false)
      }
    })

    Object.entries(updatedinvalidField).forEach(([key,value]) => {
      if (key === "num_non_fed_funded_ports"){
        expect(value).toBe(true)
      }
      else {
        expect(value).toBe(false)
      }
    })

    Object.values(updatedMissingRequiredMessage).forEach((value) => {
      expect(value).toBe(false)
    })
  });


  it('should handle the case where the number of non federal funded ports is greater than the federal ports provided', () => {
    const invalidStationValues = {...stationValues}
    invalidStationValues["num_non_fed_funded_ports"] = 1

    const mock_set_incorrect_values = vi.fn()
    portValidation(
        true,
        "num_non_fed_funded_ports",
        "non_fed_funded_ports",
        invalidStationValues,
        updatedCustomErrors,
        updatedinvalidField,
        updatedMissingRequiredMessage,
        mock_set_incorrect_values
    );

    Object.entries(updatedCustomErrors).forEach(([key,value]) => {
      if (key === "num_non_fed_funded_ports_greater_than"){
        expect(value).toBe(true)
      }
      else {
        expect(value).toBe(false)
      }
    })

    Object.entries(updatedinvalidField).forEach(([key,value]) => {
      if (key === "num_non_fed_funded_ports"){
        expect(value).toBe(true)
      }
      else {
        expect(value).toBe(false)
      }
    })

    Object.values(updatedMissingRequiredMessage).forEach((value) => {
      expect(value).toBe(false)
    })

  });


  it('should handle the case where the number of non federal funded ports is less than the federal ports provided', () => {

    const invalidStationValues = {...stationValues}
    invalidStationValues["num_non_fed_funded_ports"] = 1
    invalidStationValues["non_fed_funded_ports"] = [
      {
        "port_id":"123",
        "port_type":"DCFC"
      },
      {
        "port_id":"1234",
        "port_type":"DCFC"
      }
    ]

    const mock_set_incorrect_values = vi.fn()
    portValidation(
        true,
        "num_non_fed_funded_ports",
        "non_fed_funded_ports",
        invalidStationValues,
        updatedCustomErrors,
        updatedinvalidField,
        updatedMissingRequiredMessage,
        mock_set_incorrect_values
    );

    Object.entries(updatedCustomErrors).forEach(([key,value]) => {
      if (key === "num_non_fed_funded_ports_less_than"){
        expect(value).toBe(true)
      }
      else {
        expect(value).toBe(false)
      }
    })

    Object.entries(updatedinvalidField).forEach(([key,value]) => {
      if (key === "num_non_fed_funded_ports"){
        expect(value).toBe(true)
      }
      else {
        expect(value).toBe(false)
      }
    })

    Object.values(updatedMissingRequiredMessage).forEach((value) => {
      expect(value).toBe(false)
    })
  });

  it('should handle the case where the number of non federal funded ports is null, but non federal ports are listed', () => {
    const invalidStationValues = {...stationValues}
    invalidStationValues["num_non_fed_funded_ports"] = null
    invalidStationValues["non_fed_funded_ports"] = [
      {
        "port_id":"11",
        "port_type":""
      }
    ]
    const mock_set_incorrect_values = vi.fn()
    portValidation(
        true,
        "num_non_fed_funded_ports",
        "non_fed_funded_ports",
        invalidStationValues,
        updatedCustomErrors,
        updatedinvalidField,
        updatedMissingRequiredMessage,
        mock_set_incorrect_values
    );

    Object.values(updatedCustomErrors).forEach((value)=> {
      expect(value).toBe(false)
    })
    Object.entries(updatedinvalidField).forEach(([key,value]) => {
      if (key === "num_non_fed_funded_ports"){
        expect(value).toBe(true)
      }
      else {
        expect(value).toBe(false)
      }
    })
    Object.entries(updatedMissingRequiredMessage).forEach(([key,value]) => {
      if (key === "num_non_fed_funded_ports"){
        expect(value).toBe(true)
      }
      else {
        expect(value).toBe(false)
      }
    })
  });


  it('should handle the happy path case where the number of non federal funded ports equals the ports provided', () => {
    const validStationValues = {...stationValues}
    validStationValues["num_non_fed_funded_ports"] = 1
    validStationValues["non_fed_funded_ports"] = [
      {
        "port_id": "123",
        "port_type": "LC"
      }
    ]

    const mock_set_incorrect_values = vi.fn()
    portValidation(
        true,
        "num_non_fed_funded_ports",
        "non_fed_funded_ports",
        validStationValues,
        updatedCustomErrors,
        updatedinvalidField,
        updatedMissingRequiredMessage,
        mock_set_incorrect_values
    );

    // verifies that all attributes are set to false for the custom errors, invalid field, and missing required objects
    Object.values(updatedCustomErrors).forEach((value)=> {
      expect(value).toBe(false)
    })
    Object.values(updatedinvalidField).forEach((value)=> {
      expect(value).toBe(false)
    })
    Object.values(updatedMissingRequiredMessage).forEach((value)=> {
      expect(value).toBe(false)
    })
  });

// JE-7052 frontend bug ensuring that missing required fields are present in error banner
describe("checkValidData() - empty form submitted", () => {
  it('should handle case where the form is not filled out, Number of Federally Funded Ports is an invalid field but Number of Non-Federally Funded Ports is not', () => {
    const emptyStationValues = {...stationValues};
    emptyStationValues["num_fed_funded_ports"] = null;
    emptyStationValues["num_non_fed_funded_ports"] = null;
    emptyStationValues["non_fed_funded_ports"] = [];
    emptyStationValues["fed_funded_ports"] = [];

    // mocks all setters
    const mock_set_incorrect_values = vi.fn();
    const mock_set_error_subrecipients = vi.fn();
    const mock_set_error_port_ids = vi.fn();
    const mock_set_invalid_fields = vi.fn();
    const mock_set_missing_required_message = vi.fn();
    const mock_set_custom_errors = vi.fn();

    // calling checkValidData with all empty values as parameters
    checkValidData(
      emptyStationValues,
      updatedCustomErrors,
      updatedinvalidField,
      updatedMissingRequiredMessage,
      {"RegisterNonFedFundedStationFeatureFlag": true},
      false, //duplicate station error
      [], // selected subrecipients
      [], // authorized subrecipients
      [], // selected fed funded ports
      [], // selected non fed funded ports
      0, //fed funded ports
      0, // non fed funded ports
      null, //isStationFederallyFunded
      mock_set_incorrect_values,
      mock_set_error_subrecipients,
      mock_set_error_port_ids,
      mock_set_invalid_fields,
      mock_set_missing_required_message,
      mock_set_custom_errors,
    );

    // verifies that setInvalidField setter was called making sure that invalid field usestate for num fed/non_fed_funded_ports are properly assigned
    expect(mock_set_invalid_fields).toHaveBeenCalledWith(expect.objectContaining({
      "federally_funded": true,
      "num_fed_funded_ports": true,
      "num_non_fed_funded_ports": false
    }));

    // verifies that setMissingReqauiredMessage setter was called making sure that missing required message usestate for num fed/non_fed_funded_ports are properly assigned
    expect(mock_set_missing_required_message).toHaveBeenCalledWith(expect.objectContaining({
      "federally_funded": true,
      "num_fed_funded_ports": true,
      "num_non_fed_funded_ports": false
    }));
  });

});

