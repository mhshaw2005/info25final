# info25final

## Main Idea
We will be takeing data from each park about how many visitors each park has gotten over the years. We will use this data to show which parks are the most popular, which parks are the least popular, as well as showing the effect that covid had on national park visitors. We will use the location of each parks, and the size of each park to compare how size and location effect visitors.

## Data
Our data consists of the name of the national park, the coordinates, the number of visitors per certain years, and the ID. Our cleaned data has gotten rid of parks that are missing any of these pieces of data. Our number of visitors was origonally floats, so we made them into integers to make them easier to work with. We also made sure the parks had the same amount of years availible for the visitor count.

## Data Source

We obtained our data from Wikidata (https://www.wikidata.org/), an open and collaborative knowledge base that serves as a central storage repository for all kinds of structured data.

Our dataset consists of structured JSON data containing:
- Park names and unique Wikidata identifiers
- Annual visitor counts (numerical data spanning from 1910-2022, depending on the park)
- Geographic coordinates (latitude/longitude as decimal degrees)
- Park areas (in various units: acres, hectares, square kilometers, square miles)

**Data restrictions and limitations:**
- **Gaps:** Not all parks have visitor data for every year
- **Data quality:** Visitor numbers are reported as provided to Wikidata, and we cannot practically verify all their accuracies independently
- **Unit inconsistency:** Area measurements came in different units requiring conversion

**Ethics considerations:** 
- The data contains no personal information, only aggregate visitor statistics
- All data is publicly available and crowd-sourced

**Pros and cons of accessibility:**
- **Pros:** Completely free, open access, well-documented API, machine-readable format
- **Cons:** Data completeness varies between parks, relies on crowd-sourced accuracy, rate limiting restrictions

## API
Our data collection process used a two-stage approach with the Wikidata API. First, we queried Wikidata's SPARQL endpoint to identify all US National Parks that have visitor data available, filtering out duplicates and extracting their unique identifiers. This gave us 63 parks to work with.
In the second stage, we used the Wikidata API to fetch detailed information for each park, including coordinates, visitor history by year, and area measurements. The script implemented rate limiting and retry logic. We also built in unit conversion to standardize all area measurements, handling various units like hectares, square kilometers, and square miles.
This approach provided us with clean, standardized data to analyze how the pandemic might have affected visitation patterns across different parks and regions.

## Visuals
Individual Park Visitors Bar Plot
<img width="640" height="480" alt="Image" src="https://github.com/user-attachments/assets/fa08bee2-fa0d-46de-b3a6-dad8886fb718" />
<img width="640" height="480" alt="Image" src="https://github.com/user-attachments/assets/c0c153a6-f9fc-4bd2-908e-34a64d5f70e5" />
<img width="640" height="480" alt="Image" src="https://github.com/user-attachments/assets/09b45fc6-4c7a-4dd7-ac67-abf9df31fffa" />

These three plots show the total number of visitors at individual National Parks/Reserves in one year. When saving these images, the names of the National Parks are cut off which renders them basically unreadable. Because the same parks didn't report their visitor numbers in all three years, I was unable to code an order for the parks to appear on the x-axis. For these two reasons, these plots were left out of the final presentation, until McKenna (me) accidentally got stuck on them during the question period. 
These plots do have some interesting information. Many parks had very little change in their visitor numbers between 2019 and 2020. Black Canyon of the Gunnison, Crater Lake National Park, Everglades National Park, Bryce Canyon, and Dry Tortugas National Park, all had noteably more visitors in 2020 than 2019. Conagree National Park, Capitol Reef National Park, Carlsbad Caverns National Park, Glacier Bay National Park and Preserve, and Biscayne National Park all had noteably fewer visitors in 2020 than 2021. In 2021, the visitor count for Cuyahoga Valley National Park, which had been somewhat constant between 2019-2020, skyrocketed along with the Everglades National Park attendence. 
Further investigation into the conditions of each park in each year and the visitor count for each park in each year would be needed to determine if the COVID-19 pandemic caused lower/higher visitor attendence to each National Park. 


<img width="640" height="480" alt="Image" src="lineGraph.png" />

The above graph shows the total number of visitors to each park every 10 years. This is able to show us the progerssion of visitors through-out the years. It also is great to show the differece in growth rate from the 1910-2020.

<img width="640" height="398" alt="Image" src="API_and_Seaborn_Plots/Plot_line_average.png" />

This plot shows a focused look at the parks (those with available data for all the years shown) and the changes from the preceding years to 2020. It averaged all these parks visitor counts over the year to show a general trend over time for parks across the nation.

<img width="640" height="398" alt="Image" src="API_and_Seaborn_Plots/Plot_combo_box_strip.png" />

This visualization shows the distribution of visitors across the parks for each year. It uses a log scale to get a better sense of the movement and deviation from the preexisting trend before 2020. It shows each quartile, the median, and individual parks.

<img width="640" height="398" alt="Image" src="API_and_Seaborn_Plots/Plot_violin.png" />

This visualization uses a violin plot, intuitively similar to a histogram, to get a sense of the distribution density of park visitors across different years. Notice how the 2020 distribution shows both a lower peak and a compression of the densest area toward fewer visitors, representing the widespread impact on park visitation that year.

<img width="640" height="640" alt="Image" src="Geographic_Visualizations/map_visitors_2010.png" />

This geographic visualization shows us the baseline number of visitors for the year 2010, with every park represented and more popular National Parks are shown as darker red/orange. The visually noticeable and popular ones include Great Smoky Mountains, Yosemite, and Grand Canyon National Parks.

<img width="640" height="640" alt="Image" src="Geographic_Visualizations/map_change_absolute_2019_vs_2020.png" />

This visualization shows the absolute amount of decrease in visitors from 2019 to 2020, only showing parks where data is available. The darker red represents a bigger drop in visitor count. The biggest difference is noticeable in Yosemite, Glacier, Rocky Mountain and Gateway Arch National Parks.

<img width="640" height="640" alt="Image" src="Geographic_Visualizations/map_change_percent_2019_vs_2020.png" />

This geographic visualization shows the percent decrease of visitors from 2019 to 2020, and compared to the previous map it more clearly shows proportionally large drops in Alaska and Hawaii. It is even visible now to see small increase in visitors across the Northeast and US Virgin Islands.

<img width="640" height="640" alt="Image" src="Geographic_Visualizations/map_density_2020.png" />

This visualization shows the visitor density of National Parks during Covid (ratio of visitors in the year 2020 and area of the park). Darker blue represents parks with more visitors per unit area. Parks in the Eastern US are relatively packed, while the Northern Contiguous US and Alaska are much sparser. The values are represented in a nonlinear fashion to increase visual contrast.



## Conclusion
In conclusion, the US National Parks did experience a decline in total number of visitors during the 2020 pandemic. This phenomenon was not equally distributed across all parks, though, as some experienced a growth in popularity during the pandemic. THe US mainland National Parks were the only ones to grow in popularity, likley because air travel was limited during the pandemic. The data used for this project does not have sufficient data to determine if the lockdown was the cause of the observed changes in visitor numbers. The main limitation to our analysis is that only 16 of 60+ parks recorded visitor population for 2019, and fewer recorded visitor counts in 2020 and 2021. A year-by-year account of each National Park, their specific type of recreation and their accessibility to visitors in terms of travel and recreation level would be needed in order to make this conclusion. 
