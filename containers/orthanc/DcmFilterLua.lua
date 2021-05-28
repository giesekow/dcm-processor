function ReceivedInstanceFilter(dicom, origin, info)
   local ActionSource = dicom.ActionSource
   -- Only allow incoming CT images
   if dicom.Modality == 'CT' then
   	return true
   -- Only allow incoming MR images
   elseif dicom.Modality == 'MR' then
      return true
   -- Only allow incoming dcm-processed images
   elseif dicom.ActionSource ~= nil then
      return true
   else
      -- PrintRecursive(dicom)
   	return false
   end
end