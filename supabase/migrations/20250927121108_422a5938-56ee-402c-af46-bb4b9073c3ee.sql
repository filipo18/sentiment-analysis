-- Create RLS policy to allow public read access to main_reddit table for dashboard
CREATE POLICY "Allow public read access to main_reddit" 
ON public.main_reddit 
FOR SELECT 
USING (true);

-- Create RLS policy for main_youtube table as well
CREATE POLICY "Allow public read access to main_youtube" 
ON public.main_youtube 
FOR SELECT 
USING (true);