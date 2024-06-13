TARGET = os.getenv("DATA") or "/tmp/nifti"
DBPATH = "/tmp/db.sqlite3"
LOGPATH = os.getenv("LOGS") or "/logs"
LOGLEVEL = tonumber(os.getenv("LOGLEVEL") or '1')
MININSTANCES = 3

SUPPORTED_MODALITY = os.getenv("SUPPORTED_MODALITY") or "CT,MR"

JUNK_FILES = os.getenv("JUNK_FILES") or {"sbi","surv","bersi","racker","ssde","results", "mip", "mono", "spectal", "scout", "localizer", "lokali", "konturen", "sectrareconstruction", "zeffect", "iodoinekein", "smartplan", "doseinf"}
ACCEPTED_FILES = os.getenv("ACCEPTED_FILES") or "primary"
INSTANCE_REQUIRED_TAGS = os.getenv("INSTANCE_REQUIRED_TAGS") or {"SeriesInstanceUID", "InstanceNumber", "ImageOrientationPatient", "ImagePositionPatient"}

function LogInfo(tag, msg)
   local timestamp = os.date('%Y-%m-%d %H:%M:%S')
   local filename = LOGPATH .. "/orthanc_" .. os.date('%Y-%m-%d') .. ".log"
   local fullmessage = "* " .. timestamp .. ":: " .. msg

   fullmessage = string.gsub(fullmessage, '"', '\\"')
   tag = string.gsub(tag, '"', '\\"')

   os.execute('echo "[' .. tag .. ']' .. fullmessage .. '" >> ' .. filename)
end

function GetLogInfo(header, addInstance)
   addInstance = addInstance or false
   local info = "[" .. (header.PatientID or '') .. " -> " .. (header.StudyDescription or '') .. " -> " .. (header.SeriesDescription or '') .. "(" .. (header.SeriesNumber or '') ..")"

   if addInstance then
      info = info .. " -> " .. (header.InstanceNumber or '')
   end

   info = info .. "]"
   return info
end

function SendToScheduler(data)

   local http = require("socket.http")
   local ltn12 = require"ltn12"

   local urlAddress = os.getenv("SCHEDULER_HOST") .. ':' .. os.getenv("SCHEDULER_PORT") .. '/stable-patient'

   local body = {}
   local jsonData = DumpJson(data)

   local res, code, headers, status = http.request {
      method = "POST",
      url = urlAddress,
      source = ltn12.source.string(jsonData),
      headers = {
         ["content-type"] = "application/json",
         ["content-length"] = string.len(jsonData)
      },
      sink = ltn12.sink.table(body),
   }

end

function Sleep(n)
   os.execute("sleep " .. tonumber(n))
end

function AddSeriesToDB(seriesId, patientId)

   local sqlite3 = require("lsqlite3complete")
   local db = sqlite3.open(DBPATH)

   db:exec[=[
      CREATE TABLE IF NOT EXISTS series (series_id TEXT NOT NULL, patient_id TEXT NOT NULL);
      CREATE INDEX patient_id_index ON series (patient_id);
   ]=]

   local sql = "INSERT INTO series VALUES ('" .. seriesId .. "', '" .. patientId .."')"
   db:execute(sql)

   db:close()

end

function RemovePatientFromDB(patientId)
   local sqlite3 = require("lsqlite3complete")
   local db = sqlite3.open(DBPATH)

   db:exec[=[
      CREATE TABLE IF NOT EXISTS series (series_id TEXT NOT NULL, parent_id TEXT NOT NULL);
      CREATE INDEX patient_id_index ON series (patient_id);
   ]=]

   local selectSQL = "SELECT series_Id FROM series WHERE patient_id = '" .. patientId .."'"
   local deleteSQL = "DELETE FROM series WHERE patient_id = '" .. patientId .."'"

   local series = {}
   local hasData = false
   
   for seriesId in db:urows(selectSQL) do
      series[seriesId] = true
      hasData = true
   end

   db:execute(deleteSQL);

   db:close()
   
   if hasData then
      return series
   end

   return nil

end

function ToAscii(s)
   -- http://www.lua.org/manual/5.1/manual.html#pdf-string.gsub
   -- https://groups.google.com/d/msg/orthanc-users/qMLgkEmwwPI/6jRpCrlgBwAJ
   return s:gsub('[^a-zA-Z0-9-/-: ]', '_')
end

function Contains(m, k)
   return m[k] ~= nil
end

function Split(pString, pPattern)
   local Table = {}  -- NOTE: use {n = 0} in Lua-5.0
   local fpat = "(.-)" .. pPattern
   local last_end = 1
   local s, e, cap = pString:find(fpat, 1)
   while s do
      if s ~= 1 or cap ~= "" then
     table.insert(Table,cap)
      end
      last_end = e+1
      s, e, cap = pString:find(fpat, last_end)
   end
   if last_end <= #pString then
      cap = pString:sub(last_end)
      table.insert(Table, cap)
   end
   return Table
end

function MaybeSplit(v, sep)
   if type(v) == "string" then return Split(v, sep) end
   return v
end

function IsManufacturer(header, manufacturer)
   if not Contains(header, "Manufacturer") then return false end
   return string.lower(header["Manufacturer"]) == string.lower(manufacturer)
end

function IsMultiFrameDicom(header)
   if (not Contains(header, "MediaStorageSOPClassUID")) and (not Contains(header, "SOPClassUID")) then return false end

   local tagValue = header["MediaStorageSOPClassUID"] or header["SOPClassUID"]

   local expValues = {"1.2.840.10008.5.1.4.1.1.4.1", "1.2.840.10008.5.1.4.1.1.4", "1.2.840.10008.5.1.4.1.1.2.1", "1.2.840.10008.5.1.4.1.1.2"}
   
   for i, v in pairs(expValues) do
      if tagValue == v then return true end
   end

   if Contains(header, "SharedFunctionalGroupsSequence") then
      if #(MaybeSplit(header["SharedFunctionalGroupsSequence"], "\\")) > 1 then return true end
   end

   if Contains(header, "PerFrameFunctionalGroupsSequence") then
      if #(MaybeSplit(header["PerFrameFunctionalGroupsSequence"], "\\")) > 1 then return true end
   end

   return false

end

function GetFullHeader(instance)
   local tags = ParseJson(RestApiGet('/instances/' .. instance .. '/simplified-tags'))
   local headers = ParseJson(RestApiGet('/instances/' .. instance .. '/header'))

   for k, v in pairs(headers) do
      tags[v["Name"]] = v["Value"]
   end

   return tags
end

function IsValidImagingDicom(header, instance)
   if IsManufacturer(header, 'philips') then
      if IsMultiFrameDicom(header) then
         return true
      end
   end

   local reqTags = {"SeriesInstanceUID", "InstanceNumber", "ImageOrientationPatient", "ImagePositionPatient"}

   for i, tg in pairs(reqTags) do
      if not Contains(header, tg) then
         if LOGLEVEL >= 2 then
            LogInfo("info", GetLogInfo(header, true) .. " Skipping instance because it does not contain on of the following tags [" .. table.concat(reqTags, ", ") .. "]: " .. instance)
         end
         return false
      end
   end

   if #(MaybeSplit(header["ImageOrientationPatient"], "\\")) < 6 then
      if LOGLEVEL >= 2 then
         LogInfo("info", GetLogInfo(header, true) .. " Skipping instance because ImageOrientationPatient has less than 6 entries : " .. instance)
      end
      return false
   end

   if #(MaybeSplit(header["ImagePositionPatient"], "\\")) < 3 then
      if LOGLEVEL >= 2 then
         LogInfo("info", GetLogInfo(header, true) .. " Skipping instance because ImagePositionPatient has less than 3 entries : " .. instance)
      end
      return false
   end

   if Contains(header, "ImageType") then
      local imtype = string.lower(table.concat(MaybeSplit(header["ImageType"], "\\"), ","))
      local junkType = {"LOCALIZER", "OTHER"}

      for i, jt in pairs(junkType) do
         if string.match(imtype, string.lower(jt)) then
            if LOGLEVEL >= 2 then
               LogInfo("info", GetLogInfo(header, true) .. " Skipping instance because ImageType has one of entries [" .. table.concat(junkType, ", ") .. "] : " .. instance)
            end
            return false
         end
      end
   end

   return true

end

function CheckInstances(instances)
   local items = {}

   for i, instance in pairs(instances) do

      local header = GetFullHeader(instance)
      
      if not (header.DcmProcessorStatus == "processed" or header.SeriesDescription == "dcm-processor-temp" or header.ActionSource == "dcm-processor") then
         local isValid = IsValidImagingDicom(header, instance)
         if isValid then
            table.insert(items, instance)
         end
      else
         if LOGLEVEL >= 2 then
            LogInfo("info", GetLogInfo(header, true) .. " Skipping instance because it either processed, temporary or from dcm-processor: " .. instance)
         end
      end

   end

   return items

end

function CheckImageType(header)

   if Contains(header, "ImageType") then
      local imageType = header["ImageType"]
      local imtype = string.lower(table.concat(MaybeSplit(imageType, "\\"), ","))
      local junkType = MaybeSplit(JUNK_FILES, ",")
      local accpType = MaybeSplit(ACCEPTED_FILES, ",")

      local accepted = false

      for i, acc in pairs(accpType) do
         if string.match(imtype, string.lower(acc)) then
            accepted = true
            break
         end
      end

      if not accepted then
         return false
      end

      for i, jt in pairs(junkType) do
         if string.match(imtype, string.lower(jt)) then
            return false
         end
      end

      return true
   end

   return false
end

function CheckModality(header)

   if Contains(header, "Modality") then
      local modality = string.lower(header["Modality"])
      local sups = MaybeSplit(SUPPORTED_MODALITY, ",")

      local accepted = false

      for i, sup in pairs(sups) do
         if string.match(modality, string.lower(sup)) then
            accepted = true
            break
         end
      end

      return accepted
   end

   return false

end

function ProcessSeries(seriesId, patientId)

   local series = ParseJson(RestApiGet('/series/' .. seriesId))
   local instances = series['Instances']

   instances = CheckInstances(instances)

   if #(instances) < MININSTANCES then
      LogInfo("info", "Skipping series because it has less than " .. MININSTANCES .. " acceptable instances: " .. seriesId)
      return false, nil
   end

   local header = GetFullHeader(instances[1])

   -- check processed
   if header.DcmProcessorStatus == "processed" or header.SeriesDescription == "dcm-processor-temp" or header.ActionSource == "dcm-processor" then
      LogInfo("info", GetLogInfo(header) .. " Skipping series because it either processed, temporary or from dcm-processor: " .. seriesId )
      return false, nil
   end

   if (not CheckImageType(header)) or (not CheckModality(header)) then
      LogInfo("info", GetLogInfo(header) .. " Skipping series it failed image type and modality check: " .. seriesId )
      return false, nil
   end

   local dcmpath = ToAscii(TARGET .. '/dicom/' .. patientId .. '/' .. seriesId)

   os.execute('mkdir -p "' .. dcmpath .. '"')

   for i, instance in pairs(instances) do
      -- Retrieve the DICOM file from Orthanc
      local dicom = RestApiGet('/instances/' .. instance .. '/file')      
      -- Write to the file
      local target = assert(io.open(dcmpath .. '/' .. instance .. '.dcm', 'wb'))
      target:write(dicom)
      target:close()
   end

   local item = {}
   item["id"] = seriesId
   item["tags"] = header

   return true, item

end

function OnStableSeries(seriesId, tags, metadata)
   local series = ParseJson(RestApiGet('/series/' .. seriesId))
   local studyId = series['ParentStudy']
   local instances = series['Instances']
   
   local header = GetFullHeader(instances[1])

   if header.DcmProcessorStatus == "processed" or header.SeriesDescription == "dcm-processor-temp" or header.ActionSource == "dcm-processor" then
      LogInfo("info", GetLogInfo(header) .. " Skipping series because it either processed, temporary or from dcm-processor: " .. seriesId)
      return
   end

   local study = ParseJson(RestApiGet('/studies/' .. studyId))
   local patientId = study["ParentPatient"]
   AddSeriesToDB(seriesId, patientId)
end

function OnStablePatient(patientId, tags, metadata)
   -- Wait for all stable series to be written
   Sleep(5)

   local newSeries = RemovePatientFromDB(patientId)

   if not newSeries then
      return
   end

   print("Stable patient received: " .. patientId)
   LogInfo("info", "Stable patient received: " .. patientId)

   local data = {}
   local patient = ParseJson(RestApiGet('/patients/' .. patientId))
   local studyIds = patient['Studies']
   local studies = {}
   local acceptedStudies = {}
   local acceptedSeries = {}
  
   for st, studyId in pairs(studyIds) do
      local study = ParseJson(RestApiGet('/studies/' .. studyId))

      local seriesIds =  study['Series']
      local series = {}

      for se, seriesId in pairs(seriesIds) do
         
         if not Contains(newSeries, seriesId) then
            break
         end

         local can_process, item = ProcessSeries(seriesId, patientId)
         if can_process then
            table.insert(series, item)
            table.insert(acceptedSeries, seriesId)
         end

      end

      if series and #(series) > 0 then
         local studyItem = {}
         studyItem["id"] = studyId
         studyItem["series"] = series
         studyItem["tags"] = study["MainDicomTags"]
         table.insert(studies,studyItem)
         table.insert(acceptedStudies, studyId)
      end

   end

   if studies and #(studies) > 0 then
      data["id"] = patientId
      data["studies"] = studies
      data["seriesIds"] = acceptedSeries
      data["studyIds"] = acceptedStudies
      data["tags"] = patient["MainDicomTags"]
      data["dcmpath"] = ToAscii('dicom/' .. patientId)

      print("Sending patient to scheduler: " .. patientId)
      LogInfo("info", "Sending patient to scheduler: " .. patientId)
      SendToScheduler(data)
   else
      print("No applicable studies/series in patient: " .. patientId)
      LogInfo("info", "No applicable studies/series in patient: " .. patientId)
   end

end

function OnStoredInstance(instanceId, tags, metadata, origin)

   local requestOrigin = origin["RequestOrigin"]

   if requestOrigin == "RestApi" then
      
      local ActionSource = tags["ActionSource"]
      local Action = tags["Action"]
      local ActionDestination = tags["ActionDestination"]

      if ActionSource == "dcm-processor" then
         if Action == 'store-data' and ActionDestination then
            if LOGLEVEL >= 2 then
               LogInfo("info", GetLogInfo(tags, true) .. "Storing Data From " .. ActionSource .. " To " .. ActionDestination)
            end
            RestApiPost("/modalities/" .. ActionDestination .. "/store", instanceId)
         end
      end

   end

end

function ReceivedInstanceFilter(dicom, origin, info)
   
   if dicom.ActionSource == "dcm-processor" or dicom.SeriesDescription == "dcm-processor-temp" then
      return true
   end

   local reqTags = MaybeSplit(INSTANCE_REQUIRED_TAGS, ",")

   for i, tg in pairs(reqTags) do
      if not Contains(dicom, tg) then
         if LOGLEVEL >= 2 then
            LogInfo("info", GetLogInfo(dicom, true) .. " Skipping instance because it does not contain on of the following tags [" .. table.concat(reqTags, ", ") .. "]")
         end
         return false
      end
   end

   return true
end
