// Improved RunPod face swap function with better error handling and memory management
async function runPodFaceSwap(
  targetImageUrl: string,
  sourceImageUrl: string,
  targetFaceIndex: number
): Promise<string> {
  
  if (!RUNPOD_API_KEY) {
    throw new Error("RUNPOD_API_KEY not configured");
  }
  
  // Validate image URLs before sending to RunPod
  if (!targetImageUrl.startsWith('http') || !sourceImageUrl.startsWith('http')) {
    throw new Error("Invalid image URLs provided");
  }
  
  console.log(`[RunPod] Starting face swap - target face index: ${targetFaceIndex} (1-based, left-to-right)`);
  
  const requestData = {
    input: {
      source_url: sourceImageUrl,        // User's face image URL
      target_url: targetImageUrl,        // Scene image URL
      source_index: 1,                   // Always 1 (single user face)
      target_index: targetFaceIndex      // 1-based left-to-right index from Face++
    }
  };
  
  try {
    // Add timeout and retry logic
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 120000); // 2 minute timeout
    
    const response = await fetch(RUNPOD_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${RUNPOD_API_KEY}`,
      },
      body: JSON.stringify(requestData),
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    
    // Log response details for debugging
    console.log(`[RunPod] Response status: ${response.status}`);
    console.log(`[RunPod] Response headers:`, Object.fromEntries(response.headers.entries()));
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error(`[RunPod] API error (${response.status}):`, errorText);
      
      // Handle specific RunPod error codes
      if (response.status === 503) {
        throw new Error("RunPod service temporarily unavailable - please try again");
      } else if (response.status === 429) {
        throw new Error("RunPod rate limit exceeded - please wait and try again");
      } else if (response.status === 413) {
        throw new Error("Image too large for RunPod processing - please use smaller images");
      } else {
        throw new Error(`RunPod API error: ${response.status} - ${errorText}`);
      }
    }
    
    const result = await response.json();
    console.log(`[RunPod] Raw response:`, JSON.stringify(result, null, 2));
    
    // Validate response structure
    if (!result.output) {
      console.error("[RunPod] No output in response:", result);
      throw new Error("RunPod API returned invalid response format");
    }
    
    if (!result.output.success) {
      const errorMessage = result.output.message || "Unknown RunPod error";
      console.error("[RunPod] Face swap failed:", errorMessage);
      
      // Handle specific error messages
      if (errorMessage.includes("memory") || errorMessage.includes("OOM")) {
        throw new Error("RunPod worker ran out of memory - try with smaller images");
      } else if (errorMessage.includes("timeout")) {
        throw new Error("RunPod processing timeout - please try again");
      } else if (errorMessage.includes("face")) {
        throw new Error(`RunPod face detection error: ${errorMessage}`);
      } else {
        throw new Error(`RunPod face swap failed: ${errorMessage}`);
      }
    }
    
    if (!result.output.image_base64) {
      console.error("[RunPod] No image_base64 in response:", result.output);
      throw new Error("RunPod API did not return an image");
    }
    
    console.log("[RunPod] Face swap completed successfully");
    return `data:image/png;base64,${result.output.image_base64}`;
    
  } catch (error: any) {
    if (error.name === 'AbortError') {
      throw new Error("RunPod request timeout - please try again");
    }
    
    console.error("[RunPod] Request failed:", error);
    throw error; // Re-throw the error to be handled by the caller
  }
}

// Helper function to validate and potentially resize images before sending to RunPod
async function validateImageForRunPod(imageUrl: string): Promise<boolean> {
  try {
    const response = await fetch(imageUrl, { method: 'HEAD' });
    const contentLength = response.headers.get('content-length');
    
    if (contentLength) {
      const sizeInMB = parseInt(contentLength) / (1024 * 1024);
      console.log(`[RunPod] Image size: ${sizeInMB.toFixed(2)} MB`);
      
      // RunPod typically has a 10MB limit
      if (sizeInMB > 10) {
        console.warn(`[RunPod] Image too large: ${sizeInMB.toFixed(2)} MB`);
        return false;
      }
    }
    
    return true;
  } catch (error) {
    console.warn(`[RunPod] Could not validate image size:`, error);
    return true; // Proceed anyway
  }
}

// Updated usage in your main function
async function useRunPodWithValidation(
  targetImageUrl: string,
  sourceImageUrl: string,
  targetFaceIndex: number
): Promise<string> {
  
  // Validate images before processing
  const targetValid = await validateImageForRunPod(targetImageUrl);
  const sourceValid = await validateImageForRunPod(sourceImageUrl);
  
  if (!targetValid || !sourceValid) {
    throw new Error("Images too large for RunPod processing");
  }
  
  return await runPodFaceSwap(targetImageUrl, sourceImageUrl, targetFaceIndex);
}