import streamlit as st
import requests
import json
import re
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Function to clean NIC codes
def clean_nic_codes(input_text):
    # Remove special characters and split by commas, spaces, or newlines
    cleaned = re.sub(r'[^\d,\s]', '', input_text)
    nic_codes = re.split(r'[,\s]+', cleaned)
    # Filter out empty strings
    return [code for code in nic_codes if code]

# Function to generate business objective using an external API (e.g., OpenAI)
def generate_business_objective(nic_codes_with_descriptions):
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        return "Error: API key not found. Please set the OPENAI_API_KEY environment variable."
    
    # Format NIC codes with descriptions for prompt
    nic_details = []
    for nic, description in nic_codes_with_descriptions:
        nic_details.append(f"NIC {nic}: {description}")
    
    nic_details_string = "\n".join(nic_details)
    
    # Craft the prompt for the API
    prompt = f"""Generate a comprehensive business objective with the following NIC codes and their descriptions:

{nic_details_string}

The objective should:
1. Include a separate paragraph for each NIC code
2. Be detailed and comprehensive for each business activity described
3. Do not include the NIC code number at the end of each paragraph (as per NIC Code XXXXX)
4. Use professional business language
5. Avoid any special characters
6. Maximum characters in total need to be restricted to 4000

Format requirements:
- Start each paragraph with "To carry on the business of..." or similar appropriate phrasing
- Do not start with first person refernece but keep it general. For example, never write with "Our objective", but keep it in a sense of what company does concisely.
- Make each NIC code's objective a separate paragraph
- Be comprehensive yet concise
- Base the objective directly on the business type/description provided for each NIC code
"""

    # Call the OpenAI API
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You are a specialized business document generator that creates comprehensive business objectives based on NIC codes and their descriptions."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 1500
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            data=json.dumps(payload)
        )
        
        if response.status_code == 200:
            result = response.json()
            generated_text = result["choices"][0]["message"]["content"]
            return generated_text
        else:
            return f"Error: API call failed with status code {response.status_code}. Response: {response.text}"
    
    except Exception as e:
        return f"Error generating objective: {str(e)}"

# Set up the Streamlit app
st.set_page_config(
    page_title="NIC Business Objective Generator",
    page_icon="🏢",
    layout="wide"
)

st.title("NIC Business Objective Generator")
st.write("Generate comprehensive business objectives based on NIC codes and business type")

# Reminder about environment variable
if not os.getenv('OPENAI_API_KEY'):
    st.warning("Please ensure the OPENAI_API_KEY environment variable is set before running this application.")

# Input form
with st.form("nic_form"):
    # Input for multiple NIC codes and descriptions
    st.subheader("Enter NIC Code(s) and Description(s)")
    st.write("For multiple NIC codes, enter one code and description per line")
    
    # Using a single text area for input with example format
    nic_input = st.text_area(
        "Enter each NIC code followed by its description, one per line",
        height=150,
        help="Format: NIC_CODE - Description\nExample:\n62099 - Other information technology and computer services activities\n62020 - Computer consultancy and facilities management",
        placeholder="62099 - Other information technology and computer services activities\n62020 - Computer consultancy and facilities management\n62011 - Writing, modifying, testing of computer program"
    )
    
    # Submit button
    submit_button = st.form_submit_button("Generate Objective")

# Process the form submission
if submit_button:
    if not nic_input:
        st.error("Please enter NIC codes with descriptions")
    else:
        # Parse the input to extract NIC codes and descriptions
        lines = nic_input.strip().split('\n')
        nic_codes_with_descriptions = []
        
        for line in lines:
            # Extract NIC code and description using regex or simple split
            if '-' in line:
                parts = line.split('-', 1)  # Split on first hyphen only
                nic_code = parts[0].strip()
                description = parts[1].strip() if len(parts) > 1 else ""
                
                # Clean the NIC code to ensure it's just digits
                nic_code = re.sub(r'[^\d]', '', nic_code)
                
                if nic_code and description:
                    nic_codes_with_descriptions.append((nic_code, description))
        
        if not nic_codes_with_descriptions:
            st.error("Could not parse any valid NIC codes with descriptions. Please use the format: 'NIC_CODE - Description'")
        elif not os.getenv('OPENAI_API_KEY'):
            st.error("OPENAI_API_KEY environment variable is not set. Please set it before running the application.")
        else:
            with st.spinner("Generating comprehensive business objective..."):
                # Generate the objectives using the API
                generated_objective = generate_business_objective(nic_codes_with_descriptions)
                
                # Display the NIC codes used
                st.subheader("NIC Codes")
                for nic, desc in nic_codes_with_descriptions:
                    st.write(f"**{nic}**: {desc}")
                
                # Display the generated objectives
                st.subheader("Generated Business Objective")
                st.text_area("Complete Objective", generated_objective, height=400)
                
                # Add download button for the generated objective
                st.download_button(
                    label="Download Objective as Text",
                    data=generated_objective,
                    file_name="business_objective.txt",
                    mime="text/plain"
                )

# Show example at the bottom
with st.expander("View Example Objectives"):
    st.markdown("""
    ### Example 1: Information Technology Related
    **Input:**
    ```
    62099 - Other information technology and computer services activities n.e.c 
    62020 - Computer consultancy and computer facilities management activities
    62011 - Writing, modifying, testing of computer program to meet the needs of a particular client excluding web-page designing
    ```
    
    **Generated Objective:**
    
    To engage in IT-enabled services including software as a service, platform as a service, infrastructure as a service, business process outsourcing, knowledge process outsourcing, and IT infrastructure management. This includes the development, maintenance, and operation of IT infrastructure, data centers, cloud solutions, and networking services. The company may also provide software licensing, training, workshops, and certification programs in software development, AI, and cybersecurity as per NIC Code 62099.
    
    To provide computer consultancy and computer facilities management services, including system integration, IT infrastructure management, network security, enterprise resource planning, and data center operations. The company shall offer managed IT services, cloud computing solutions, IT support, software deployment, and maintenance services for enterprises. This includes consulting on IT strategy, cybersecurity risk assessment, compliance management, disaster recovery solutions, and optimizing IT infrastructure performance for businesses as per NIC Code 62020.
    
    To carry on the business of software development, IT consulting, and technology solutions, including but not limited to designing, developing, testing, maintaining, and deploying software applications, mobile applications, web-based platforms, and enterprise solutions. This includes providing custom software development, system integration, and IT support services to businesses across various industries as per NIC Code 62011.
    
    ### Example 2: Consultancy and Travel Services
    **Input:**
    ```
    70200 – Management consultancy activities
    52291 – Activities of travel agents and tour operators
    52231 - Actives related to air transport of passengers, animals or freight
    ```
    
    **Generated Objective:**
    
    To carry on the business of management consultancy activities, including strategic planning, business process optimization, financial advisory, organizational restructuring, market research, risk management, and operational efficiency improvement. The company shall provide consultancy services in areas such as business development, corporate governance, human resource management, digital transformation, and project management to enterprises across various industries to enhance their growth and competitiveness as per NIC Code 70200.
    
    To engage in the activities of travel agents and tour operators, including planning, organizing, and facilitating domestic and international travel for individuals, groups, and corporate clients. The company shall provide services such as ticket booking, itinerary planning, travel insurance, visa assistance, holiday packages, accommodation arrangements, transportation bookings, and other related travel services. Additionally, the company shall collaborate with hotels, airlines, and other service providers to offer customized travel experiences as per NIC Code 52291.
    
    To carry on activities related to the air transport of passengers, animals, or freight, including air cargo handling, passenger assistance, baggage handling, logistics coordination, chartered flight services, and airport ground support services. The company shall provide solutions for air freight forwarding, customs clearance, and international trade facilitation. Additionally, it shall engage in partnerships with airlines, logistics companies, and airport authorities to ensure seamless and efficient air transport operations as per NIC Code 52231.
    """)

st.markdown("---")
st.caption("This application generates comprehensive business objectives based on NIC codes and their descriptions using AI.")
